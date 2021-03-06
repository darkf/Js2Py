// Copyright (c) 2012 Ecma International.  All rights reserved.
// Ecma International makes this code available under the terms and conditions set
// forth on http://hg.ecmascript.org/tests/test262/raw-file/tip/LICENSE (the
// "Use Terms").   Any redistribution of this code must retain the above
// copyright and this notice and otherwise comply with the Use Terms.

/*---
es5id: 15.2.3.5-4-9
description: >
    Object.create - argument 'Properties' is a Number object whose
    primitive value is any interesting number (15.2.3.7 step 2).
includes: [runTestCase.js]
---*/

function testcase() {

        var props = new Number(12);
        var result = false;

        Object.defineProperty(props, "prop", {
            get: function () {
                result = this instanceof Number;
                return {};
            },
            enumerable: true
        });
        Object.create({}, props);
        return result;
    }
runTestCase(testcase);
