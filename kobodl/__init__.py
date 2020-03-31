import click

from kobodl.app import app

@click.group()
@click.option('--fmt', type=click.STRING, default='psql')
@click.version_option()
@click.pass_context
def cli(ctx, fmt):
    ctx.obj = {'fmt': fmt}


@click.command(name='serve')
@click.option('-h', '--host', type=click.STRING)
@click.option('-p', '--port', type=click.INT)
@click.option('--debug', is_flag=True)
@click.option(
    '-o',
    '--output-dir',
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    default='kobo_downloads',
)
@click.pass_context
def serve(ctx, host, port, debug, output_dir):
    app.config['output_dir'] = output_dir
    app.run(host, port, debug)


cli.add_command(serve)

from kobodl.commands import (  # noqa: F401 E402
    user,
    book,
)
