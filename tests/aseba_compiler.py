# This file is part of tdmclient.
# Copyright 2022 ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE,
# Miniature Mobile Robots group, Switzerland
# Author: Yves Piguet
#
# SPDX-License-Identifier: BSD-3-Clause

"""Compile Aseba source code to bytecode using package "dukpy" and
vpl-web's compiler in JavaScript.
"""

import dukpy
import json

class AsebaCompiler:

    def __init__(self, path_vpl="../../vpl-web/src/"):

        self.src_preamble = ""
        for filename in (
            "a3a-ns.js",
            "compiler-ns.js",
            "compiler-vm.js",
            "compiler.js",
            "compiler-macros.js",
            "compiler-thymio.js",
        ):
            with open(path_vpl + filename) as f:
                self.src_preamble += f.read()

        self.src_preamble += """
var asebaSourceCode =
"""
        self.src_postamble = """
;
var asebaNode = new A3a.A3aNode(A3a.thymioDescr);
var c = new A3a.Compiler(asebaNode, asebaSourceCode);
c.functionLib = A3a.A3aNode.stdMacros;
var bytecode = c.compile();
print("all var", JSON.stringify(c.asebaNode.variables.concat(c.declaredVariables)))
JSON.stringify([
    bytecode,
    c.asebaNode.variables.concat(c.declaredVariables)
])
"""

    def compile(self, aseba_src_code):
        """Compile Aseba source code and return a dict with bytecode in "bc"
        and array of variables ({name:string,size:int,offset:int}) in "variables"
        """
        src = self.src_preamble + json.dumps(aseba_src_code) + self.src_postamble
        return json.loads(dukpy.evaljs(src))
