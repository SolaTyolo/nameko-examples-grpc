import pytest
import redis

from products.dependencies import REDIS_URI_KEY


@pytest.fixture
def redis_config():
    return {REDIS_URI_KEY: 'redis://user:password@localhost:6379/11'}


@pytest.fixture
def config(rabbit_config, redis_config):
    config = rabbit_config.copy()
    config.update(redis_config)
    return config


@pytest.yield_fixture
def redis_client(config):
    client = redis.StrictRedis.from_url(
        config.get(REDIS_URI_KEY), decode_responses=True
    )
    yield client
    client.flushdb()


@pytest.fixture
def product():
    return {
        'id': 'LZ127',
        'title': 'LZ 127',
        'passenger_capacity': 72,
        'maximum_speed': 130,
        'in_stock': 11,
    }


@pytest.fixture
def create_product(redis_client, product):
    def create(**overrides):
        new_product = product.copy()
        new_product.update(**overrides)
        redis_client.hmset(
            'products:{}'.format(new_product['id']),
            new_product)
        return new_product
    return create


@pytest.fixture
def products(create_product):
    return [
        create_product(
            id='LZ127',
            title='LZ 127 Graf Zeppelin',
            passenger_capacity=20,
            maximum_speed=128,
            in_stock=10,
        ),
        create_product(
            id='LZ129',
            title='LZ 129 Hindenburg',
            passenger_capacity=50,
            maximum_speed=135,
            in_stock=11,
        ),
        create_product(
            id='LZ130',
            title='LZ 130 Graf Zeppelin II',
            passenger_capacity=72,
            maximum_speed=135,
            in_stock=12,
        ),
    ]
