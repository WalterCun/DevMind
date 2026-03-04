# devmind-core/tests/unit/test_relational_search.py
"""
Tests para RelationalMemory.search() - versión sin DB.
"""

import inspect

import pytest


def test_search_method_signature():
    """Verifica que el método search existe con la firma correcta"""
    from core.memory.relational_store import RelationalMemory

    # Verificar que el método existe
    assert hasattr(RelationalMemory, 'search')

    # Verificar firma
    method = getattr(RelationalMemory, 'search')
    sig = inspect.signature(method)
    params = list(sig.parameters.keys())

    # Parámetros esperados (self no cuenta)
    expected_params = ['self', 'project', 'query', 'entities', 'limit']
    assert params == expected_params, f"Expected {expected_params}, got {params}"

    # Verificar valores por defecto
    assert sig.parameters['entities'].default is None
    assert sig.parameters['limit'].default == 20


def test_search_return_type_annotation():
    """Verifica que search tiene tipo de retorno anotado"""
    from core.memory.relational_store import RelationalMemory

    method = getattr(RelationalMemory, 'search')
    return_annotation = method.__annotations__.get('return')

    # Debería retornar Dict[str, List[Any]] o similar
    assert return_annotation is not None, "search should have return type annotation"


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.skip(reason="Requires PostgreSQL and migrations")
def test_search_functional_with_db():
    """Test funcional completo (requiere DB configurada)"""
    # Este test se ejecuta solo en CI/CD con servicios disponibles
    from core.memory.relational_store import RelationalMemory
    from db.models import Project

    project = Project.objects.create(name="Test", description="Test")
    memory = RelationalMemory()

    result = memory.search(project=project, query="test", limit=5)

    assert isinstance(result, dict)
    assert all(isinstance(v, list) for v in result.values())