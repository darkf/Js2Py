// Copyright (c) 2012 Ecma International.  All rights reserved.
// Ecma International makes this code available under the terms and conditions set
// forth on http://hg.ecmascript.org/tests/test262/raw-file/tip/LICENSE (the
// "Use Terms").   Any redistribution of this code must retain the above
// copyright and this notice and otherwise comply with the Use Terms.

/*---
es5id: 15.2.3.6-4-103
description: >
    Object.defineProperty - 'name' and 'desc' are data properties,
    name.writable and desc.writable are different values (8.12.9 step
    12)
includes: [propertyHelper.js]
---*/

var obj = {};

Object.defineProperty(obj, "foo", {
    writable: false, configurable: true
});

Object.defineProperty(obj, "foo", {
    writable: true
});
verifyEqualTo(obj, "foo", undefined);

verifyWritable(obj, "foo");

verifyNotEnumerable(obj, "foo");

verifyConfigurable(obj, "foo");

