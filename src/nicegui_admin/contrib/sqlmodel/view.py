from dataclasses import dataclass, field
from typing import Any, Sequence, Union, TYPE_CHECKING

from nicegui import run
from pydantic import ValidationError
from pydantic_core import PydanticUndefined
from sqlmodel import SQLModel, select
from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.orm import InstrumentedAttribute, Mapper, RelationshipProperty
from sqlalchemy.sql import Select

from nicegui_admin.contrib.sqlmodel.converters import BaseSqlModelFieldConverter, SqlModelFieldConverter
from nicegui_admin.contrib.sqlmodel.exceptions import InvalidModelError
from nicegui_admin.contrib.sqlmodel.fields import MultiplePKField
from nicegui_admin.contrib.sqlmodel.helpers import build_query, extract_column_python_type
from nicegui_admin.form import Form
from nicegui_admin.views import BaseCrudView, WHERE, ORDER_BY
from nicegui_admin.helpers import Unset, iterdecode, not_none, pydantic_error_to_form_validation_errors
from nicegui_admin.fields import (
    BaseField,
    # ColorField, # ToDo: check if needed
    # EmailField, # ToDo: check if needed
    # FileField, # ToDo: check if needed
    # PhoneField, # ToDo: check if needed
    # RelationField, # ToDo: check if needed
    StringField,
    # TextAreaField, # ToDo: check if needed
    # URLField, # ToDo: check if needed
)

if TYPE_CHECKING:
    from nicegui_admin.contrib.sqlmodel.admin import SqlModelAdmin

_list = list
NO_VALIDATION_FIELDS = ()# (FileField, RelationField) # ToDo: check if needed


@dataclass
class SqlModelCrudView(BaseCrudView):
    """
    View class for SQLModel models.

    :param model: SQLModel model class to be used for this view.
    """

    model: type[SQLModel] = field(default=Any, repr=False)
    converter: BaseSqlModelFieldConverter | Unset = field(default=Unset, repr=False)

    def __post_init__(self):
        if self.model is Any:
            raise InvalidModelError(f"Model is required for {self.__class__.__name__}")
        converter: BaseSqlModelFieldConverter = Unset.resolve(self.converter, SqlModelFieldConverter())
        self.fields = converter.convert_fields_list(fields=self.fields,
                                                    model=self.model)

        # Detect the primary key attribute(s) of the model
        _pk_attrs = []
        self._pk_column: Union[tuple[InstrumentedAttribute, ...], InstrumentedAttribute] = ()
        self._pk_coerce: Union[tuple[type, ...], type] = ()
        for key in list(self.model.__dict__.keys()):
            attr = getattr(self.model, key)
            if isinstance(attr, InstrumentedAttribute) and getattr(attr, "primary_key", False):
                _pk_attrs.append(key)
        if len(_pk_attrs) == 0:
            raise InvalidModelError(f"No primary key found in model {self.model.__name__}")
        elif len(_pk_attrs) == 1:
            self._pk_column = getattr(self.model, _pk_attrs[0])
            self._pk_coerce = extract_column_python_type(self._pk_column)  # type: ignore[arg-type]
            try:
                # Try to find the primary key field among the fields
                self.pk_field = next(f for f in self.fields if f.name == _pk_attrs[0])
            except StopIteration:
                # If the primary key is not among the fields, treat its value as a string
                self.pk_field = StringField(_pk_attrs[0], type=self._pk_column.type)  # ToDo: type is needed
        else:
            self._pk_column = tuple(getattr(self.model, attr) for attr in _pk_attrs)
            self._pk_coerce = tuple(extract_column_python_type(c) for c in self._pk_column)
            self.pk_field: BaseField = MultiplePKField(pk_attrs=_pk_attrs, _type=tuple([t.type for t in self._pk_column]))
        super().__post_init__()

    @property
    def admin(self) -> Union["SqlModelAdmin", Any, None]:
        return super().admin

    async def count_query(self,
                          where: WHERE = None) -> Select:
        """
        Return a Select expression which is used for count

        :param where: WHERE clause to filter the count query. It can be either a dict or a string representing the full text search term.
        :return: SQLAlchemy Select expression
        """

        # select
        statement = select(func.count()).select_from(self.model)

        # where
        if where is not None:
            if isinstance(where, dict):
                where = build_query(where, self.model)
            else:
                where = await self.build_full_text_search_query(where, self.model)
            statement = statement.where(where)

        return statement

    async def count(self,
                    where: WHERE = None) -> int:
        with self.admin.session() as session:
            # build query
            statement = await self.count_query(where)

            # execute query
            result = await run.io_bound(session.execute, statement)

            # process result
            result = result.scalar_one()

            return result

    async def list_query(self,
                         offset: int = 0,
                         limit: int = 100,
                         where: WHERE = None,
                         order_by: ORDER_BY = None) -> Select:
        """
        Return a Select expression which is used for list

        :param offset: Offset for pagination
        :param limit: Limit for pagination
        :param where: WHERE clause to filter the list query. It can be either a dict or a string representing the full text search term.
        :param order_by: ORDER BY clause to sort the list query. It should be a list of strings in the format "attr_name ASC|DESC".
        :return: SQLAlchemy Select expression
        """

        # select
        statement = select(self.model)

        # limit
        if limit > 0:
            statement = statement.limit(limit)

        # offset
        if offset > 0:
            statement = statement.offset(offset)

        # where
        if where is not None:
            if isinstance(where, dict):
                where = build_query(where, self.model)
            else:
                where = await self.build_full_text_search_query(where, self.model)
            statement = statement.where(where)

        # order_by
        order_by = order_by or []
        for value in order_by:
            attr_key, order = value.strip().split(maxsplit=1)
            model_attr = getattr(self.model, attr_key, None)
            if model_attr is not None and isinstance(model_attr.property, RelationshipProperty):
                statement = statement.outerjoin(model_attr)
            sorting_attr = self.sortable_field_mapping.get(attr_key, model_attr)
            if order.lower() == "desc":
                statement = statement.order_by(not_none(sorting_attr).desc())
            else:
                statement = statement.order_by(sorting_attr)

        # join
        # for field in self.get_fields_list(RequestAction.LIST): # ToDo: check if needed
        #     if isinstance(field, RelationField):
        #         statement = statement.options(joinedload(getattr(self.model, field.name)))

        return statement

    async def list(self,
                   fields: Sequence[BaseField],
                   offset: int = 0,
                   limit: int = 100,
                   where: WHERE = None,
                   order_by: ORDER_BY = None) -> _list[dict[str, Any]]:
        with self.admin.session() as session:
            # build query
            statement = await self.list_query()

            # execute query
            objs = await run.io_bound(session.execute, statement)

            # process objects
            objs = objs.scalars().unique().all()

            # serialize objects
            obj_serialized_dicts = []
            for obj in objs:
                obj_dict = obj.model_dump()
                obj_serialized_dict = await self._data_from_model(data=obj_dict,
                                                                  fields=fields)
                obj_serialized_dicts.append(obj_serialized_dict)

            return obj_serialized_dicts

    async def detail_query(self,
                           pk: str) -> Select:
        """
        Return a Select expression which is used for details

        :param pk: Primary key of the detail query
        :return: SQLAlchemy Select expression
        """

        # select
        statement = select(self.model)

        # where
        if isinstance(self._pk_column, tuple):
            """
            For composite primary keys, the pk parameter is a comma-separated string
            representing the values of each primary key attribute.

            For example, if the model has two primary keys (id1, id2):
            - the `pk` will be: "val1,val2"
            - the generated query: (id1 == val1 AND id2 == val2)
            """
            assert isinstance(self._pk_coerce, tuple)
            clauses = []
            for _pk_col, _coerce, _pk in zip(self._pk_column, self._pk_coerce, iterdecode(pk)):
                if _coerce is not bool:
                    clauses.append(_pk_col == _coerce(_pk))
                else:
                    clauses.append(_pk_col == (_pk == "True"))
            statement = statement.where(and_(*clauses))
        else:
            assert isinstance(self._pk_coerce, type)
            statement = statement.where(self._pk_column == self._pk_coerce(pk))

        # join
        # for field in self.get_fields_list(request, request.state.action): ToDo: check if needed
        #     if isinstance(field, RelationField):
        #         statement = statement.options(joinedload(getattr(self.model, field.name)))

        return statement

    async def detail(self,
                     fields: Sequence[BaseField],
                     pk: str) -> dict[str, Any] | None:
        with self.admin.session() as session:
            # build query
            statement = await self.detail_query(pk=pk)

            # execute query
            obj = await run.io_bound(session.execute, statement)

            # process object
            obj = obj.scalars().unique().one_or_none()

            # serialize object
            obj_serialized_dict = None
            if obj:
                obj_dict = obj.model_dump()
                obj_serialized_dict = await self._data_from_model(data=obj_dict,
                                                                  fields=fields)

            return obj_serialized_dict

    async def create(self,
                     fields: Sequence[BaseField],
                     form: Form) -> dict[str, Any] | None:
        try:
            with self.admin.session() as session:
                # validate data
                await self.validate(fields=fields,
                                    data=form.data)

                # deserialize data
                deserialized_data = await self._data_to_model(data=form.data,
                                                              fields=fields)
                obj = self.model(**deserialized_data)

                # add to session and commit
                session.add(obj)
                session.commit()

                # refresh object
                session.refresh(obj)

                # serialize object
                obj_dict = obj.model_dump()
                obj_serialized_dict = await self._data_from_model(data=obj_dict,
                                                                  fields=fields)
        except Exception as exc:
            return self.handle_exception(exc=exc, form=form)
        return obj_serialized_dict

    async def edit_query(self,
                         pk: str) -> Select:
        """
        Return a Select expression which is used for editing

        :param pk: Primary key of the edit query
        :return: SQLAlchemy Select expression
        """

        # select
        statement = select(self.model)

        # where
        if isinstance(self._pk_column, tuple):
            """
            For composite primary keys, the pk parameter is a comma-separated string
            representing the values of each primary key attribute.

            For example, if the model has two primary keys (id1, id2):
            - the `pk` will be: "val1,val2"
            - the generated query: (id1 == val1 AND id2 == val2)
            """
            assert isinstance(self._pk_coerce, tuple)
            clauses = []
            for _pk_col, _coerce, _pk in zip(self._pk_column, self._pk_coerce, iterdecode(pk)):
                if _coerce is not bool:
                    clauses.append(_pk_col == _coerce(_pk))
                else:
                    clauses.append(_pk_col == (_pk == "True"))
            statement = statement.where(and_(*clauses))
        else:
            assert isinstance(self._pk_coerce, type)
            statement = statement.where(self._pk_column == self._pk_coerce(pk))

        # join
        # for field in self.get_fields_list(request, request.state.action): ToDo: check if needed
        #     if isinstance(field, RelationField):
        #         statement = statement.options(joinedload(getattr(self.model, field.name)))

        return statement

    async def edit(self,
                   fields: Sequence[BaseField],
                   pk: str,
                   form: Form) -> dict[str, Any] | None:
        try:
            with self.admin.session() as session:
                # validate data
                await self.validate(fields=fields,
                                    data=form.data)

                # deserialize data
                deserialized_data = await self._data_to_model(data=form.data,
                                                              fields=fields)
                # build query
                statement = await self.detail_query(pk=pk)

                # execute query
                obj = await run.io_bound(session.execute, statement)

                # process object
                obj = obj.scalars().unique().one_or_none()
                if not obj:
                    raise ValueError(f"No such primary key: {pk}")

                # update object
                for model_field_name, model_field in self.model.model_fields.items():
                    if model_field_name in deserialized_data:
                        value = deserialized_data[model_field_name]
                    else:
                        if model_field.default != PydanticUndefined:
                            value = model_field.default
                        elif model_field.default_factory:
                            value = model_field.default_factory()
                        else:
                            value = None
                    setattr(obj, model_field_name, value)

                # add to session and commit
                session.add(obj)
                session.commit()

                # refresh objects
                session.refresh(obj)

                # serialize objects
                obj_dict = obj.model_dump()
                obj_serialized_dict = await self._data_from_model(data=obj_dict,
                                                                  fields=fields)
        except Exception as exc:
            return self.handle_exception(exc=exc, form=form)
        return obj_serialized_dict

    async def delete(self,
                     pk: str) -> bool:
        raise NotImplementedError()

    # def search_query(self, term: str) -> Any:
    #     """
    #     Return SQLAlchemy whereclause to use for full text search
    #
    #     :param term: search term
    #     :return: SQLAlchemy whereclause to use for full text search
    #
    #     Args:
    #        request: Starlette request
    #        term: Filtering term
    #
    #     Examples:
    #        ```python
    #        class PostView(ModelView):
    #
    #             def get_search_query(self, request: Request, term: str):
    #                 return Post.title.contains(term)
    #        ```
    #     """
    #
    #     clauses = []
    #     for field in self.get_fields_list(request):
    #         if field.searchable and type(field) in [
    #             StringField,
    #             TextAreaField,
    #             EmailField,
    #             URLField,
    #             PhoneField,
    #             ColorField,
    #         ]:
    #             attr = getattr(self.model, field.name)
    #             clauses.append(cast(attr, String).ilike(f"%{term}%"))
    #     return or_(*clauses)

    # async def build_full_text_search_query(self, request: Request, term: str, model: Any) -> Any:
    #     return self.get_search_query(request, term)


    async def validate(self,
                       fields: Sequence[BaseField],
                       data: dict[str, Any]) -> None:
        fields_to_exclude = []
        for f in fields:
            if not isinstance(f, NO_VALIDATION_FIELDS): # ToDo: check if needed
                continue
            fields_to_exclude.append(f.name)

        validated_data = {k: v for k, v in data.items() if k not in fields_to_exclude}

        self.model.model_validate(validated_data)

    def handle_exception(self,
                         exc: Exception,
                         form: Form) -> None:
        if isinstance(exc, ValidationError):
            exc = pydantic_error_to_form_validation_errors(exc)

        # try:
        #     """Automatically handle sqlalchemy_file error"""
        #     from sqlalchemy_file.exceptions import ValidationError
        #
        #     if isinstance(exc, ValidationError):
        #         raise FormValidationError({exc.key: exc.msg})
        # except ImportError:  # pragma: no cover
        #     pass

        return super().handle_exception(exc=exc,
                                        form=form)
