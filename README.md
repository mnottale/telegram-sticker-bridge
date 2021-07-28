Telegram sticker HTTP bridge
============================

HTTP server that serves and caches telegram stickers.

So you have all those nice telegram stickers, and you'd love to use them on
discord, slack, etc? This is the solution.

Dependencies and requirements
-----------------------------

- python modules: PIL
- installed packages: imagemagick (convert)
- (optional) docker and docker image tgs-to-gif for animated stickers
- A telegram bot: create one using @botfather, and copy the bot key to the file ".botkey".
- "mkdir cache"

Deployment
----------

It is recommended to run a nginx as reverse proxy in front of this program, since
it uses http.server which is not meant for production.

Just run it and it will start accepting HTTP requests on port 8989 (edit sources
to change it).

Referencing stickers
--------------------

When referencing a sticker set, you must use it's "id name" which is not
the same thing as the displayed name in telegram. To obtain it, click on
"share stickers". That will put a link in your clipboard. Paste it somewhere
and you will get a link of the form https://t.me/addstickers/SOMETHING . That
SOMETHING is the sticker real id name.


Routes
------

- /STICKERSET/INDEX : Reply with a png image of sticker INDEX of STICKERSET
- /STICKERSET/INDEX/2 : Reply with downsized sticker by a factor 2.
- /STICKERSET : Reply with a png image of the whole stickerset. Can take some time on first call.
- /STICKERSET/map : Same as above, but each image of the set is clickable and will redirect to the clicked sticker
- /listall : Clickable list of all complete stickersets cached.
- /showall : Clickable images of all stickerset cached.