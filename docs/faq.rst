FAQ
===

This is a list of Frequently Asked Questions about UgandaSMS. Feel
free to suggest new entries!

How do I..
----------

... handle messages that do not match any parser?

    Subscribe to the :data:`router.transports.post_route` signal and
    make a query to test if there were no forms::

      def need_help(sender=None, **kwargs):
          if sender.forms.count() == 0:
             outgoing = Outgoing(
                 text=u"We did not understand your text. Do you need help?",
                 uri=sender.message.uri)
             outgoing.save()

      post_route.connect(need_help, sender=Incoming)

    Note that there is no ``reply`` method, because there is nothing
    to reply to.
