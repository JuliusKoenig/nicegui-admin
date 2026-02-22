from typing import Any, Sequence, Union, TYPE_CHECKING

from sqlmodel import SQLModel, select

from niceguitools.admin.views import CrudView, WHERE, ORDER_BY
from niceguitools.admin.helper import Unset

if TYPE_CHECKING:
    from niceguitools.admin.contrib.sqlmodel.admin import SqlModelAdmin


class SqlModelCrudView(CrudView):
    def __init__(self,
                 *,
                 model: type[SQLModel],
                 path: str = Unset,
                 title: str = Unset,
                 icon: str | None = Unset):
        """
        :param model: SQLModel model class to be used for this view.
        :param path: Path to the view. If not provided, it will be generated from the class name.
        :param title: Title of the view to be displayed.
        :param icon: Icon to be displayed for this view.
        """

        super().__init__(path=path,
                         title=title,
                         icon=icon)

        self.model: type[SQLModel] = model

    @property
    def admin(self) -> Union["SqlModelAdmin", Any]:
        return super().admin

    async def count(self,
                    where: WHERE = None) -> int:
        raise NotImplementedError()

    async def list(self,
                   offset: int = 0,
                   limit: int = 100,
                   where: WHERE = None,
                   order_by: ORDER_BY = None) -> Sequence[dict[str, Any]]:
        with self.admin.session() as session:
            # Todo: implement where
            # Todo: implement order_by
            objs = session.exec(
                select(self.model)
                .offset(offset)
                .limit(limit)
            ).all()
            obj_dicts = []
            for obj in objs:
                obj_dicts.append(obj.model_dump())
            return obj_dicts


    async def get(self,
                  pk: Any) -> dict[str, Any] | None:
        result = await self.list(limit=1,
                                 where={"pk": pk})
        return result[0] if result else None

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
