import os
import asyncio
import aioredis
import aiohttp.web
import aiohttp_jinja2
import gino
import jinja2
from sqlalchemy.engine.url import URL
import uvloop
import config
from models import db
from routes import routes


if __name__ == '__main__':
    # Создание каталога для хранения кадров, полученных с камер
    if not os.path.exists(config.path_camera_captures):
        os.mkdir(config.path_camera_captures)

    # Использование UVLoop в качестве цикла событий по-умолчанию
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    # Конфигурация сервера
    loop = asyncio.get_event_loop()
    app = aiohttp.web.Application(loop=loop, debug=True)
    app.router.add_routes(routes)
    app.router.add_static('/static', config.path_static_files)
    app['config'] = {
        'path_camera_captures': config.path_camera_captures
    }
    aiohttp_jinja2.setup(app=app, loader=jinja2.FileSystemLoader(config.path_template_files))

    # Конфигурация драйвера базы данных (PostgreSQL)
    app.middlewares.append(db)
    app['config']['gino'] = {
        'dsn': URL(
            drivername=config.postgres_driver,
            host=config.postgres_host,
            port=config.postgres_port,
            username=config.postgres_username,
            password=config.postgres_password,
            database=config.postgres_database)
    }
    db.init_app(app)

    # Инициализация подключений к сторонним приложениям после старта сервера
    async def init_connections(*args, **kwargs):
        global app
        # Подключение к PostgreSQL и инициализация таблиц базы данных
        engine = await gino.create_engine(app['config']['gino']['dsn'])
        await db.set_bind(engine, loop=loop)
        await db.gino.create_all()
        # Выполнение всех сопутствующих *.sql скриптов
        for sql_filename in os.listdir(config.path_sql_scripts):
            if not sql_filename.endswith('.sql'):
                continue
            sql_path = os.path.join(config.path_sql_scripts, sql_filename)
            with open(sql_path, 'r') as sql_file:
                scripts = sql_file.read().split('\n\n\n')
                for script in scripts:
                    script = script.strip()
                    if script:
                        await engine.status(script)
        # Подключение к Redis
        app['redis'] = await aioredis.create_redis_pool(address=config.redis_address,
                                                        db=config.redis_database,
                                                        password=config.redis_password)
    app.on_startup.append(init_connections)

    # Завершение соединений со сторонними приложениями после остановки сервера
    async def close_connections(*args, **kwargs):
        global app
        # Завершение соединения с Redis
        app['redis'].close()
        await app['redis'].wait_closed()
    app.on_shutdown.append(close_connections)

    # Запуск сервера
    aiohttp.web.run_app(app, host=config.server_host, port=config.server_port)
