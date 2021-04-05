class RequestMaker:
    def __init__( self ):
        self._nextId = 0

    def makeRequest( self, method, params ):
        currId = self._nextId

        self._nextId += 1

        return {
            'id': currId,
            'method': method,
            'params': params
        }

    def makeNotify( self, method, params ):
        return {
            'method': method,
            'params': params
        }

    def makeResponse( self, id, result, error = None ):
        if params is None:
            return {
                'id': id,
                'error': error
            }
        else:
            return {
                'id': id,
                'result': result
            }
