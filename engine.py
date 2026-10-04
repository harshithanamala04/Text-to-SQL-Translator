# Root proxy for engine.py
import os
import sys
import importlib.util

sub_engine = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Text-to-SQL-Translator", "engine.py")
spec = importlib.util.spec_from_file_location("sub_engine", sub_engine)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

universal_sql_engine = mod.universal_sql_engine
explain_sql = mod.explain_sql
clean_input_text = mod.clean_input_text
parse_num = mod.parse_num

__all__ = ["universal_sql_engine", "explain_sql", "clean_input_text", "parse_num"]
