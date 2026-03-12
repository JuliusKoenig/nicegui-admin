from dataclasses import dataclass, field
from typing import Any, Sequence, Union, TYPE_CHECKING

from nicegui import run
from sqlmodel import SQLModel, select
from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.orm import InstrumentedAttribute, Mapper, RelationshipProperty
from sqlalchemy.sql import Select

from nicegui_admin.contrib.sqlmodel.converters import BaseSqlModelFieldConverter, SqlModelFieldConverter
from nicegui_admin.contrib.sqlmodel.exceptions import InvalidModelError
from nicegui_admin.contrib.sqlmodel.fields import MultiplePKField
from nicegui_admin.contrib.sqlmodel.helpers import build_query, extract_column_python_type
from nicegui_admin.views import BaseCrudView, WHERE, ORDER_BY
from nicegui_admin.helpers import Unset, iterdecode, not_none
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


@dataclass
class SqlModelCrudView(BaseCrudView):
    """
    View class for SQLModel models.

    :param model: SQLModel model class to be used for this view.
    """

    model: type[SQLModel] = field(default=Unset, repr=False)
    converter: BaseSqlModelFieldConverter | Unset = field(default=Unset, repr=False)

    def __post_init__(self):
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
                self.pk_field = StringField(_pk_attrs[0], type=self._pk_column.type) # ToDo: type is needed
        else:
            self._pk_column = tuple(getattr(self.model, attr) for attr in _pk_attrs)
            self._pk_coerce = tuple(extract_column_python_type(c) for c in self._pk_column)
            self.pk_field: BaseField = MultiplePKField(pk_attrs=_pk_attrs, _type=tuple([t.type for t in self._pk_column]))
        super().__post_init__()

    @property
    def admin(self) -> Union["SqlModelAdmin", Any, None]:
        return super().admin

    def count_query(self) -> Select:
        """
        Return a Select expression which is used for count

        :return: SQLAlchemy Select expression
        """

        return select(func.count()).select_from(self.model)

    async def count(self,
                    where: WHERE = None) -> int:
        with self.admin.session() as session:
            statement = self.count_query()
            if where is not None:
                if isinstance(where, dict):
                    where = build_query(where, self.model)
                else:
                    where = await self.build_full_text_search_query(where, self.model)
                statement = statement.where(where)
            return await run.io_bound(session.execute, statement).scalar_one()

    def list_query(self) -> Select:
        """
        Return a Select expression which is used for list

        :return: SQLAlchemy Select expression
        """

        return select(self.model)

    def list_order_clauses(self, order_list: list[str], stmt: Select) -> Select:
        for value in order_list:
            attr_key, order = value.strip().split(maxsplit=1)
            model_attr = getattr(self.model, attr_key, None)
            if model_attr is not None and isinstance(model_attr.property, RelationshipProperty):
                stmt = stmt.outerjoin(model_attr)
            sorting_attr = self.sortable_field_mapping.get(attr_key, model_attr)
            if order.lower() == "desc":
                stmt = stmt.order_by(not_none(sorting_attr).desc())
            else:
                stmt = stmt.order_by(sorting_attr)
        return stmt

    async def list(self,
                   offset: int = 0,
                   limit: int = 100,
                   where: WHERE = None,
                   order_by: ORDER_BY = None) -> Sequence[dict[str, Any]]:
        with self.admin.session() as session:
            statement = self.list_query()
            if limit > 0:
                statement = statement.limit(limit)
            if offset > 0:
                statement = statement.offset(offset)
            if where is not None:
                if isinstance(where, dict):
                    where = build_query(where, self.model)
                else:
                    where = await self.build_full_text_search_query(where, self.model)
                statement = statement.where(where)
            statement = self.list_order_clauses(order_by or [], statement)
            # for field in self.get_fields_list(RequestAction.LIST): # ToDo: check if needed
            #     if isinstance(field, RelationField):
            #         statement = statement.options(joinedload(getattr(self.model, field.name)))
            result = await run.io_bound(session.execute, statement)
            obj_dicts = []
            for obj in result.scalars().unique().all():
                obj_dicts.append(obj.model_dump())
            return obj_dicts

    def detail_query(self) -> Select:
        """
        Return a Select expression which is used for details

        :return: SQLAlchemy Select expression
        """

        return select(self.model)

    async def detail(self,
                     pk: Any) -> dict[str, Any] | None:
        with self.admin.session() as session:
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
                clause = and_(*clauses)
            else:
                assert isinstance(self._pk_coerce, type)
                clause = self._pk_column == self._pk_coerce(pk)
            statement = self.detail_query().where(clause)
            # for field in self.get_fields_list(request, request.state.action): ToDo: check if needed
            #     if isinstance(field, RelationField):
            #         statement = statement.options(joinedload(getattr(self.model, field.name)))

            result = await run.io_bound(session.execute, statement)
            obj = result.scalars().unique().one_or_none()
            return obj.model_dump() if obj else None

    async def create(self,
                     *data: dict[str, Any]) -> dict[str, Any] | Sequence[dict[str, Any]]:
        with self.admin.session() as session:
            objs = []
            for item in data:
                obj = self.model(**item)
                objs.append(obj)
                session.add(obj)
            session.commit()
            for obj in objs:
                session.refresh(obj)
            return objs if len(objs) > 1 else objs[0]

    async def edit(self,
                   *pks: Any,
                   data: dict[str, Any]) -> dict[str, Any] | Sequence[dict[str, Any]]:
        raise NotImplementedError()

    async def delete(self,
                     *pks: Any) -> bool | Sequence[bool]:
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
