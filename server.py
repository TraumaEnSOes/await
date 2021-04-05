import ast
import asyncio
import os
import sys

class DirCursorServer:
    ErrorInMessage = ( str( { 'key':'Error','error':'Fail when try parse message' } ) + '\n' ).encode( 'utf8' )

    @staticmethod
    def parseInput( msg ):
        realMsg = None

        try:
            realMsg = ast.literal_eval( msg, dict )

        except KeyboardInterrupt as err:
            raise err

        except:
            pass

        return realMsg


    @staticmethod
    async def connect_stdin_stdout( ):
        loop = asyncio.get_event_loop( )
        reader = asyncio.StreamReader( )
        protocol = asyncio.StreamReaderProtocol( reader )
        await loop.connect_read_pipe( lambda: protocol, sys.stdin )
        w_transport, w_protocol = await loop.connect_write_pipe( asyncio.streams.FlowControlMixin, sys.stdout )
        writer = asyncio.StreamWriter( w_transport, w_protocol, reader, loop )

        return reader, writer


    async def run( self ):
        self._stdin, self._stdout = await DirCursorServer.connect_stdin_stdout( )

        helloMsg = str( { 'method':'hello' } ) + '\n'
        helloMsg = helloMsg.encode( 'utf8' )

        self._stdout.write( helloMsg )
        await self._stdout.drain( )

        while True:
            msg = await self._stdin.readline( )

            if not msg:
                break

            realMsg = DirCursorServer.parseInput( msg )

            if realMsg is None:
                self._stdout.write( DirCursorServer.ErrorInMessage )
                await self._stdout.drain( )
                continue

            self._stdout.write( msg )
            await self._stdout.drain( )


async def main( ):
    server = DirCursorServer( )

    await server.run( )

if __name__ == "__main__":
    server = DirCursorServer( )

    asyncio.run( server.run( ) )

