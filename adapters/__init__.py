from . import inosmi_ru
from .exceptions import ArticleNotFound, AdapterNotImplemented

__all__ = ['SANITIZERS', 'ArticleNotFound', 'AdapterNotImplemented']

SANITIZERS = {
    'inosmi_ru': inosmi_ru.sanitize,
}
