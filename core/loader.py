import importlib
import inspect
import pkgutil


def load_instances_from_directory(
    directory: str,
    package_name: str,
    base_class: type,
    *args,
):
    instances = []
    for module_info in sorted(
        pkgutil.walk_packages(path=[directory], prefix=f"{package_name}."),
        key=lambda item: item.name,
    ):
        if module_info.ispkg:
            continue
        module_name = module_info.name.rsplit(".", maxsplit=1)[-1]
        if module_name.startswith("__"):
            continue

        module = importlib.import_module(module_info.name)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj is base_class:
                continue
            if not issubclass(obj, base_class):
                continue
            instances.append(obj(*args))
    return instances
