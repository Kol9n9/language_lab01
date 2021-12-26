from wsgiref.simple_server import make_server
from datetime import datetime
import json

from dateutil.parser import parse
from pytz import timezone, all_timezones
from tzlocal import get_localzone

local_tz = str(get_localzone())

response_parts = [
''' 
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Time app</title>
</head>
<body>
''',
'''
</body>
</html>
'''
]

def get_ok_html(tz, time):
    return '200 OK',[
        response_parts[0],
        '<h2>Time: </h2>', time.strftime('%Y-%m-%d %H:%M:%S'),
        '<h3>Zone: </h3>', tz,
        response_parts[1]
    ]

def get_bad_html():
    return '400 BAD REQUEST', [
        response_parts[0],
        '<h2>400 BAD REQUEST</h2>',
        response_parts[1]
    ]

def get_ok_json(obj):
    return '200 OK', [json.dumps(obj)]

def get_bad_json():
    return '400 BAD REQUEST', '{ "error": "BAD REQUEST" }'

def time_app(environ, start_response):
    path = environ['PATH_INFO'][1:]
    method = environ['REQUEST_METHOD']
    headers = [('Content-type', 'text/html; charset=utf-8')]
    if not path.startswith('api') and method == 'GET':     
        try:
            if path != '':
                tz = path
            else:
                tz = local_tz
            time = datetime.now(tz= timezone(tz))

            status, body = get_ok_html(tz, time)
        except:
            status, body = get_bad_html()


    elif path.startswith('api') and method == 'POST':
        try:
            length = environ['CONTENT_LENGTH']
            if not length:
                length = 0
            else:
                length = int(length)
            body = json.loads(environ['wsgi.input'].read(length).decode('utf-8') or '{}')
            
            if 'tz' in body:
                tz = body['tz']
            else:
                tz = local_tz
                
            time = datetime.now(tz= timezone(tz))
            
            if path == 'api/v1/time':
                status, body = get_ok_json({'tz': tz, 'time': time.strftime('%H:%M:%S')})
            
            elif path == 'api/v1/date':
                status, body = get_ok_json({'tz': tz, 'date': time.strftime('%Y-%m-%d')})

            elif path == 'api/v1/datediff':
                if 'tz' in body['start']:
                    start_tz = body['start']['tz']
                else:
                    start_tz = local_tz

                start = timezone(start_tz).localize(parse(body['start']['date']))

                if 'tz' in body['end']:
                    end_tz = body['end']['tz']
                else:
                    end_tz = local_tz

                end = timezone(end_tz).localize(parse(body['end']['date'])) 

                diff = end - start

                status, body = get_ok_json({'diff': str(diff)})

            else:
                status, body = get_bad_json()
            
        except:
            status, body = get_bad_json()
 

    else:
        status, body = get_bad_html()

    start_response(status, headers)
    return [x.encode() for x in body]


if __name__ == '__main__':
    httpd = make_server('', 8080, time_app)
    print("Serving on port 8080...")
    httpd.serve_forever()