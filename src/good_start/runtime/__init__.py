from good_start.runtime._base import Runtime
from good_start.runtime._local import LocalRuntime

__all__ = ["Runtime", "LocalRuntime", "resolve_runtime"]


def resolve_runtime(*, no_container: bool = False) -> Runtime:
    """Return the appropriate runtime based on user preference.

    Default is container-based. Pass no_container=True for direct host execution.
    """
    if no_container:
        return LocalRuntime()

    # Container runtime — import here to defer engine detection
    from good_start.runtime._container import ContainerRuntime

    return ContainerRuntime()
