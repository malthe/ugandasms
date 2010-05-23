FAQ
===

This is a list of Frequently Asked Questions about UgandaSMS. Feel
free to suggest new entries!

How do I..
----------

... handle messages that do not match any parser?

    You can recognize such messages by their type; messages that do
    not match any parser remain with the type :class:`Incoming`.

    Register a handler for the :data:`post_parse` signal that listens
    to this type of message::

      post_parse.connect(my_handler, sender=Incoming)

    


