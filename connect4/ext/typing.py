def fully_qualified_type(obj_or_cls):
    if obj_or_cls is None:
        return ""

    class_type = obj_or_cls
    if not isinstance(obj_or_cls, type):
        class_type = type(obj_or_cls)

    module_name = class_type.__module__
    qualified_type_name = class_type.__qualname__
    return f"{module_name}.{qualified_type_name}"
