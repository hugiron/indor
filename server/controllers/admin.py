import aiohttp_jinja2


class AdminController(object):
    @aiohttp_jinja2.template('index.html')
    async def get_index(self, request):
        return {}

    @aiohttp_jinja2.template('login.html')
    async def get_login(self, request):
        return {}
