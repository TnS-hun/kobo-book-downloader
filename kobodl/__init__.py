import click

from kobodl.app import app
from kobodl.globals import Globals
from kobodl.settings import Settings


@click.group()
@click.option(
    '--fmt',
    type=click.STRING,
    default='simple',
    help='python-tabulate table format string',
)
@click.option(
    '--config',
    type=click.Path(dir_okay=False, file_okay=True, writable=True),
    help='path to kobodl.json config file',
)
@click.version_option()
@click.pass_context
def cli(ctx, fmt, config):
    Globals.Settings = Settings(config)
    ctx.obj = {'fmt': fmt}


@click.command(name='serve', short_help='start an http server')
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

from kobodl.commands import book, user  # isort:skip noqa: F401 E402
