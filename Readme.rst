This doc is copied from http://github.com/jbalogh/zamboni-lib#readme

This is the collection of FlightDeck's pure-python dependencies.

From your FlightDeck root, do this::

    git clone --recursive git://github.com/zalun/FlightDeck-lib.git vendor

Sit back and relax while all that downloads, then proceed on your merry way.

To keep it up to date::

    pushd vendor && git pull && git submodule update --init && popd


How FlightDeck-lib was made
---------------------------

::

    pip install -I --install-option="--home=`pwd`/vendor" --src='vendor/src' -r requirements/dev.txt

    # this step wasn't done (yet?)
    # ..delete some junk from vendor/lib/python...

    # Create the .pth file so Python can find our src libs.
    find src -type d -depth 1 >> flightdeck.pth

    # Add all the submodules.
    for f in src/*; do
        pushd $f >/dev/null && REPO=$(git config remote.origin.url) && popd > /dev/null && git submodule add $REPO $f
    done
    git add .


Using your own vendor lib
-------------------------

We add these lines to our manage.py file, since it's the entrypoint to
everything we do in FlightDeck  Adjust as you see fit. ::

    import site
    site.addsitedir('vendor')
    site.addsitedir('vendor/lib/python')

``addsitedir`` adds that directory to the Python path and looks for other
``.pth`` files in that dir.  We use a ``.pth`` in vendor to load our ``src/``
packages, and pip may have added other ``.pth`` files in ``vendor/lib/python``.
