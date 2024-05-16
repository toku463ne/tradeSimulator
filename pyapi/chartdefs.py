import os, falcon

import env

class ChartDefList:
    def on_get(self, req, resp):
        try:
            # List all txt files in the directory
            files = [f for f in os.listdir(env.CHARTDEF_DIR) if f.endswith('.json')]
            resp.media = files
            resp.status = falcon.HTTP_200
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.media = {'error': str(e)}


class ChartDef:
    def on_get(self, req, resp, filename):
        file_path = os.path.join(env.CHARTDEF_DIR, filename)

        # Security measure to ensure only files in the directory are accessible
        if os.path.commonpath([env.CHARTDEF_DIR]) == os.path.commonpath([env.CHARTDEF_DIR, file_path]) and os.path.isfile(file_path):
            resp.content_type = falcon.MEDIA_TEXT  # or 'text/plain'
            with open(file_path, 'r') as file:
                resp.body = file.read()
        else:
            raise falcon.HTTPNotFound(description="File not found.")
