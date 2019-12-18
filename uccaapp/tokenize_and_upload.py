import os.path
import sys
from argparse import ArgumentParser

from ucca.convert import from_text, to_json
from uccaapp.api import ServerAccessor

desc = """
Read input file as one line per paragraph, where paragraphs are separated by multiple newlines and an optional
<DELIMITER>.
Tokenize and upload as submitted tokenization tasks, then create annotation tasks from them.

Tokenization in Russian requires:
    pip install git+https://github.com/aatimofeev/spacy_russian_tokenizer.git
"""


class TokenizerUploader(ServerAccessor):
    def __init__(self, user_id, source_id, project_id, lang=None, **kwargs):
        super().__init__(**kwargs)
        self.set_source(source_id)
        self.set_project(project_id)
        self.set_user(user_id)

    def tokenize_and_upload(self, filename, log=None, lang=None, **kwargs):
        del kwargs
        log_h = open(log, "w", encoding="utf-8") if log else None
        prefix = os.path.splitext(os.path.basename(filename))[0].replace(" ", "_")
        with open(filename, encoding="utf-8") as f:
            for passage, text in from_text(f, passage_id=prefix, lang=lang, return_text=True):
                passage_out = self.create_passage(text=text, type="PUBLIC", source=self.source)
                task_in = dict(type="TOKENIZATION", status="SUBMITTED", project=self.project,
                               user=self.user, passage=passage_out, manager_comment=passage.ID,
                               user_comment="", parent=None, is_demo=False, is_active=True)
                tok_task_out = self.create_task(**task_in)
                tok_user_task_in = dict(tok_task_out)
                tok_user_task_in.update(to_json(passage, return_dict=True, tok_task=True))
                self.submit_task(**tok_user_task_in)
                task_in.update(parent=tok_task_out, type="ANNOTATION")
                ann_user_task_out = self.create_task(**task_in)
                print("Uploaded passage " + filename + " successfully.", file=sys.stderr)
                if log:
                    print(passage.ID, passage_out["id"], tok_task_out["id"], ann_user_task_out["id"],
                          file=log_h, sep="\t", flush=True)
        if log:
            log_h.close()

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("filename", help="text file with one line paragraph, where paragraphs are separated "
                                                "by multiple newlines and an optional <DELIMITER>")
        argparser.add_argument("-l", "--log", help="filename to write log of uploaded passages to")
        argparser.add_argument("--lang", choices=["ru", "en", "fr", "de"], default="ru",
                               help="language two-letter code, for tokenizer")
        ServerAccessor.add_project_id_argument(argparser)
        ServerAccessor.add_source_id_argument(argparser)
        ServerAccessor.add_user_id_argument(argparser)
        ServerAccessor.add_arguments(argparser)


def main(**kwargs):
    TokenizerUploader(**kwargs).tokenize_and_upload(**kwargs)


if __name__ == "__main__":
    argument_parser = ArgumentParser(description=desc)
    TokenizerUploader.add_arguments(argument_parser)
    main(**vars(argument_parser.parse_args()))
