/*
 * Passive, single-shot ChatGPT Android class inventory.
 * No method hooks, method calls on BillingClient, fields, instances, tokens,
 * credentials, prices, offer IDs, network access or checkout operations.
 *
 * Frida 16.x includes its Java bridge. This script is not bundled for v17.
 */
(function () {
    "use strict";
    var allowed = {
        "com.android.billingclient.api.BillingClient": true,
        "com.android.billingclient.api.BillingClientImpl": true,
        "com.android.billingclient.api.ProductDetails": true,
        "com.android.billingclient.api.BillingFlowParams": true,
        "com.android.billingclient.api.PurchasesUpdatedListener": true
    };
    if (typeof Java === "undefined" || !Java.available) {
        send({type: "billing_class_probe", java_available: false, loaded_classes: []});
        return;
    }
    Java.perform(function () {
        var found = {};
        Java.enumerateLoadedClasses({
            onMatch: function (name) {
                if (allowed[name] === true) {
                    found[name] = true;
                }
            },
            onComplete: function () {
                send({
                    type: "billing_class_probe",
                    java_available: true,
                    loaded_classes: Object.keys(found)
                });
            }
        });
    });
}());
