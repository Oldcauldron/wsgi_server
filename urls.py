

def urls():

    path_to_body = {
        r'^$': '/index.html',
        r'^/index(.)?[a-z]{0,4}$': '/index.html',
        r'^/base(.)?[a-z]{0,4}$$': '/base.html'
    }
    return path_to_body
