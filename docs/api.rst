.. _api:

API Documentation
=================

Getting Started
---------------

To load UCCA passages from XML files, manipulate them and write to files, use the following code template::

    from ucca.ioutil import get_passages_with_progress_bar, write_passage
    for passage in get_passages_with_progress_bar(filenames):
        ...
        write_passage(passage)

Each passage instantiates the :class:`ucca.core.Passage` class.

XML files can be downloaded from the various `UCCA corpora <https://github.com/UniversalConceptualCognitiveAnnotation>`__.

.. automodapi:: ucca.constructions
.. automodapi:: ucca.convert
.. automodapi:: ucca.core
.. automodapi:: ucca.diffutil
.. automodapi:: ucca.evaluation
.. automodapi:: ucca.ioutil
.. automodapi:: ucca.layer0
.. automodapi:: ucca.layer1
.. automodapi:: ucca.normalization
.. automodapi:: ucca.textutil
.. automodapi:: ucca.validation
.. automodapi:: ucca.visualization

