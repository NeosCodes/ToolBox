import importlib
import pkgutil
import plugins
from core.plugin_base import PluginBase
from typing import Dict, List


class PluginRegistry:
    def __init__(self):
        self._plugins: Dict[str, PluginBase] = {}
        self._load_all()

    def _load_all(self):
        for finder, pkg_name, is_pkg in pkgutil.iter_modules(plugins.__path__, plugins.__name__ + "."):
            if not is_pkg:
                continue
            module_path = f"{pkg_name}.plugin"
            try:
                mod = importlib.import_module(module_path)
            except ModuleNotFoundError:
                continue
            except Exception as e:
                print(f"[Registry] Failed to load {module_path}: {e}")
                continue

            for attr_name in dir(mod):
                obj = getattr(mod, attr_name)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, PluginBase)
                    and obj is not PluginBase
                ):
                    try:
                        instance = obj()
                        self._plugins[instance.meta.id] = instance
                        print(f"[Registry] Loaded plugin: {instance.meta.name}")
                    except Exception as e:
                        print(f"[Registry] Failed to instantiate {attr_name}: {e}")

    def all(self) -> List[PluginBase]:
        return list(self._plugins.values())

    def by_category(self) -> Dict[str, List[PluginBase]]:
        result: Dict[str, List[PluginBase]] = {}
        for p in self._plugins.values():
            result.setdefault(p.meta.category, []).append(p)
        return result

    def get(self, plugin_id: str) -> PluginBase | None:
        return self._plugins.get(plugin_id)