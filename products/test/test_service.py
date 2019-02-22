from nameko.testing.services import entrypoint_hook
from nameko.standalone.events import event_dispatcher
from nameko.testing.services import entrypoint_waiter
import pytest

from products.dependencies import NotFound
from products.service import ProductsService
from nameko_grpc.client import Client
from products.proto.products_pb2 import GetProduct, Product
from products.proto.products_pb2_grpc import productsStub


@pytest.fixture
def service_container(config, container_factory):
    container = container_factory(ProductsService, config)
    container.start()
    yield container
    container.stop()


@pytest.fixture
def client():
    client = Client(
        "//127.0.0.1:50051",
        productsStub
    )
    yield client.start()
    client.stop()


def test_get_product(create_product, service_container, client):
    stored_product = create_product()
    product = client.get(GetProduct(id=stored_product["id"]))

    assert stored_product["id"] == product.id
    assert stored_product["title"] == product.title
    assert stored_product["passenger_capacity"] == product.passenger_capacity
    assert stored_product["maximum_speed"] == product.maximum_speed
    assert stored_product["in_stock"] == product.in_stock


def test_create_product(redis_client, service_container, client, product):
    new_product = client.create(Product(
        id=product["id"],
        title=product["title"],
        passenger_capacity=product["passenger_capacity"],
        maximum_speed=product["maximum_speed"],
        in_stock=product["in_stock"]
    ))
    stored_product = redis_client.hgetall(f'products:{product["id"]}')
    for key in stored_product.keys():
        assert stored_product[key] == str(getattr(new_product, key))


def test_get_product_fails_on_not_found(service_container):

    with pytest.raises(NotFound):
        with entrypoint_hook(service_container, 'get') as get:
            get(111)


def test_list_products(products, service_container):

    with entrypoint_hook(service_container, 'list') as list_:
        listed_products = list_()

    assert products == sorted(listed_products, key=lambda p: p['id'])


def test_list_products_when_empty(service_container):

    with entrypoint_hook(service_container, 'list') as list_:
        listed_products = list_()

    assert [] == listed_products


def test_handle_order_created(
    config, products, redis_client, service_container
):

    dispatch = event_dispatcher(config)

    payload = {
        'order': {
            'order_details': [
                {'product_id': 'LZ129', 'quantity': 2},
                {'product_id': 'LZ127', 'quantity': 4},
            ]
        }
    }

    with entrypoint_waiter(service_container, 'handle_order_created'):
        dispatch('orders', 'order_created', payload)

    product_one, product_two, product_three = [
        redis_client.hgetall('products:{}'.format(id_))
        for id_ in ('LZ127', 'LZ129', 'LZ130')]
    assert b'6' == product_one[b'in_stock']
    assert b'9' == product_two[b'in_stock']
    assert b'12' == product_three[b'in_stock']
