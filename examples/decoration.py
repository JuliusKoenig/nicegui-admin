from nicegui_admin.helpers import decorate, undecorate, DecoratedMethodClass


def test_decorator(qwe: str, asd: int):
    return decorate(context="test",
                    qwe=qwe,
                    asd=asd)


def test_undecorator():
    return undecorate(context="test")


class Parent(DecoratedMethodClass):
    @property
    def decorated_methods(self):
        return self.__decorated_methods__

    @test_decorator(qwe="123", asd=456)
    def test1(self):
        print("parent test1")

    @test_decorator("qwe", asd=456)
    def test2(self):
        print("parent test2")


class Child(Parent):
    @test_undecorator()
    def test1(self):
        print("child test1")


if __name__ == "__main__":
    parent = Parent()
    child = Child()
    print()
