import click


@click.group()
@click.option('--fmt', type=click.STRING, default='psql')
@click.version_option()
@click.pass_context
def cli(ctx, fmt):
    ctx.obj = {'fmt': fmt}


from kobo_book_downloader.commands import (  # noqa: F401 E402
    user,
    book,
)
