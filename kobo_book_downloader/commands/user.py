import click
from tabulate import tabulate

from kobo_book_downloader.kobo import Kobo
from kobo_book_downloader.globals import Globals
from kobo_book_downloader.settings import User
from kobo_book_downloader import cli, actions


@click.group(name='user', short_help='user management')
def user():
    pass


@user.command(name='list', help='list users')
@click.pass_obj
def list(ctx):
    userlist = Globals.Settings.UserList.users
    headers = ['Email', 'UserKey', 'DeviceId', 'Authed']
    data = sorted(
        [
            (
                user.Email,
                user.UserKey,
                user.DeviceId,
                user.AreAuthenticationSettingsSet(),
            )
            for user in userlist
        ]
    )
    click.echo(tabulate(data, headers, tablefmt=ctx['fmt']))


@user.command(name='add', help='add new user')
@click.option(
    '--email', prompt=True, hide_input=False, type=click.STRING, help="kobo.com email."
)
@click.password_option(help="kobo.com password (not stored)")
@click.pass_obj
def add(ctx, email, password):
    user = User(Email=email)
    click.echo(
        """
    Open https://authorize.kobo.com/signin in a private/incognito window in your browser, wait till the page
    loads (do not login!) then open the developer tools (use F12 in Firefox/Chrome), select the console tab,
    and paste the following code there and then press Enter there in the browser.

    var newCaptchaDiv = document.createElement( "div" );
    newCaptchaDiv.id = "new-grecaptcha-container";
    document.getElementById( "grecaptcha-container" ).insertAdjacentElement( "afterend", newCaptchaDiv );
    grecaptcha.render( newCaptchaDiv.id, {
        sitekey: "6LeEbUwUAAAAADJxtlhMsvgnR7SsFpMm4sirr1CJ",
        callback: function( response ) { console.log( "Captcha response:" ); console.log( response ); }
    } );

    A captcha should show up below the Sign-in form. Once you solve the captcha its response will be written
    below the pasted code in the browser's console. Copy the response (the line below "Captcha response:")
    and paste it here.
    """
    )
    captcha = input('Captcha response: ').strip()
    actions.Login(user, password, captcha)
    Globals.Settings.UserList.users.append(user)
    Globals.Settings.Save()
    click.echo('Login Success. Try to list your books with `kobodl book list`')


cli.add_command(user)
