from polymorphic import PolymorphicModel as Base

# class PolymorphicModel(ModelBase):
#     def __new__(meta, name, bases, attrs):
#         kind = camelcase_to_underscore(name)
#         attrs = attrs.copy()
#         attrs.setdefault('__module__', meta.__module__)
#         args = attrs.setdefault('__mapper_args__', {})
#         args.setdefault('polymorphic_identity', kind)
#         return ModelBase.__new__(meta, name, bases, attrs)

# Base = PolymorphicModel("Base", (Model,), {})
