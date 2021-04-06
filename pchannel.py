import ast
import asyncio
import datetime
import os
import queue
import sys

import rpcproto

class ProcessChannel:
    @staticmethod
    def _parseLine( line ):
        obj = ast.literal_eval( line )
        return obj

    @staticmethod
    def _flushMessage( msg ):
        text = str( msg ) + '\n'
        return text

    def __init__( self, argv0, args, name = None ):
        self._name = name
        self._argv0 = argv0
        self._args = args
        self._requestMaker = rpcproto.RequestMaker( )

        self._responseQueue = asyncio.Queue( )
        self._requestQueue = asyncio.Queue( )
        self._notifyQueue = asyncio.Queue( )
        self._errQueue = asyncio.Queue( ) # Cola de líneas recibidas desde stderr.

    async def run( self, name = None ):
        if name is not None:
            self._name = name

        taskNamePrefix = self._argv0 if self._name is None else self._name

        self._process = await asyncio.create_subprocess_exec( self._argv0, self._args,
                                                              stdin = asyncio.subprocess.PIPE, stderr = asyncio.subprocess.PIPE, stdout = asyncio.subprocess.PIPE )

        self._errTask = asyncio.create_task( self._readErr( ), name = taskNamePrefix + '.ErrTask' )
        self._inTask = asyncio.create_task( self._readIn( ), name = taskNamePrefix + '.InTask' )

        await self._errTask
        await self._inTask

    async def _readErr( self ):
        while True:
            err = await self._process.stderr.readline( )
            await self._errQueue.put( ( datetime.datetime.now( ), err ) )

    async def _readIn( self ):
        while True:
            line = await self._process.stdout.readline( )
            message = ProcessChannel._parseLine( line.strip( ).decode( 'UTF-8' ) )

            if 'id' in message:
                if 'method' in message:
                    # Es un Request
                    await self._requestQueue.put( message )
                else:
                    # Es un Response
                    await self._responseQueue.put( message )

            else:
                # Es un Notify
                await self._notifyQueue.put( message )

    async def nextNotify( self ):
        message = await self._notifyQueue.get( )
        return message

    async def nextRequest( self ):
        message = await self._requestQueue.get( )
        return message

    async def nextResponse( self ):
        message = await self._responseQueue.get( )
        return message

    async def nextError( self ):
        message = await self._errQueue.get( )
        return message

    async def request( self, method, params ):
        message = self._requestMaker.makeRequest( method, params )
        self._process.stdin.write( ProcessChannel._flushMessage( message ) )
        await self._process.stdin.drain( )

    async def response( self, id, result, error = None ):
        message = self._requestMaker.makeResponse( id, result, error )
        self._process.stdin.write( ProcessChannel._flushMessage( message ) )
        await self._process.stdin.drain( )

    async def notify( self, method, params ):
        message = self._requestMaker.makeNotify( method, params )
        self._process.stdin.write( ProcessChannel._flushMessage( message ) )
        await self._process.stdin.drain( )

async def notifyReceived( proc ):
    while True:
        msg = await proc.nextNotify( )
        print( msg )

async def main( ):
    child = ProcessChannel( os.path.join( '/usr', 'bin', 'python3' ), ( os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), 'server.py' ) ) )
    handler = asyncio.create_task( notifyReceived( child ) )
    childRun = asyncio.create_task( child.run( ) )

    await handler

if __name__ == '__main__':
    asyncio.run( main( ) )
