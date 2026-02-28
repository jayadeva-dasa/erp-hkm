// Copyright (c) 2025, Narahari Dasa and contributors
// For license information, please see license.txt


function isNullOrUndefined(value) {
  return value === null || value === undefined || value === "";
}

frappe.ui.form.on("QZ Printer", {
  refresh(frm) {
    frm.add_custom_button(
      __("Print Expiry Label"),
      async function () {
        if (
          frm.doc.item_code &&
          frm.doc.company &&
          frm.doc.price_list &&
          frm.doc.quantity_exp
        ) {
          console.log(frm.doc.item_code);
          frappe.ui.form
            .qz_connect()
            .then(function () {
              if (isNullOrUndefined(frm.doc.manufacturing_date)) {
                frappe.msgprint({
                  title: __("Error"),
                  indicator: "red",
                  message: __("Manufacturing Date is required"),
              });
              return
              }
              if (isNullOrUndefined(frm.doc.day_after_expiry)) {
                frappe.msgprint({
                  title: __("Error"),
                  indicator: "red",
                  message: __("Day After Expiry is required"),
              });
              return
              }

              if (frm.doc.quantity_exp == 0 || isNullOrUndefined(frm.doc.quantity_exp)) {
                return
              }
                var printer = ""
                if (frm.doc.printer_name == "" || frm.doc.printer_name == null) {
                    printer = "TE210"
                }
                else {
                    printer = frm.doc.printer_name
                    .trim() 
                    .replace(/\s+/g, " ");
                }
                

              var config = qz.configs.create(printer); // Exact printer name from OS
              var print_data = [];
              var shift = 250; // Adjust shift for three stickers per row

              frappe.call({
                method:
                  "hkm.erpnext___custom.godex_print.filter_sellable_items",
                args: {
                  items: [frm.doc.item_code],
                  price_list: frm.doc.price_list,
                  company: frm.doc.company,
                },
                freeze: true,
                callback: (r) => {
                  var qty = frm.doc.quantity_exp;

                  var mfg_date = new Date(frm.doc.manufacturing_date);
                  var expiry_date = addDaysToDate(
                    mfg_date,
                    frm.doc.day_after_expiry
                  );

                  mfg_date = formatDateToDMY(mfg_date);
                  expiry_date = formatDateToDMY(expiry_date);

                  var group_string = "^XA";
                  var item_processed = 0;

                  for (var j = 0; j < qty; j += 3) {
                    for (var g = 0; g < 3; g++) {
                      if (item_processed == qty) {
                        break;
                      }

                      var xOffset = 15 + g * 20 + g * shift;
                      var yOffset = 20;

                      group_string += getgroupString(
                        r.message[0]["name"].replace(/\s+/g, " ").trim(),
                        mfg_date,
                        expiry_date,
                        xOffset,
                        yOffset
                      );

                      item_processed++;
                    }
                    if (item_processed == qty) {
                      break;
                    }
                    group_string += "^XZ\n^XA";
                  }
                  group_string += "^XZ";
                  print_data.push(group_string);

                  return qz.print(config, print_data);
                },
                error: (r) => {
                  // on error
                },
              });
            })
            .then(frappe.ui.form.qz_success)
            .catch((err) => {
              frappe.ui.form.qz_fail(err);
            });
          // frm.events.on_success(frm);
        } else {
          frappe.throw("Fields for printing Item Labels are not available.");
        }

        // Perform desired action such as routing to new form or fetching etc.
      },
      __("Utilities")
    );
    frm.add_custom_button(
      __("Print Item Codes"),
      async function () {
        if (
          frm.doc.item_code &&
          frm.doc.company &&
          frm.doc.price_list &&
          frm.doc.quantity
        ) {
          console.log(frm.doc.item_code);
          frappe.ui.form
            .qz_connect()
            .then(function () {
              var printer = ""
              if (frm.doc.printer_name == "" || frm.doc.printer_name == null) {
                  printer = "Godex G500"
              }
              else {
                  printer = frm.doc.printer_name
                  .trim() 
                  .replace(/\s+/g, " ");
              }
              

            var config = qz.configs.create(printer); // Exact printer name from OS



              var print_data = [];
              var shift = 310;
              frappe.call({
                method:
                  "hkm.erpnext___custom.godex_print.filter_sellable_items",
                args: {
                  items: [frm.doc.item_code],
                  price_list: frm.doc.price_list,
                  company: frm.doc.company,
                },

                freeze: true,
                callback: (r) => {
                  console.log(r.message);
                  var items_detailed = r.message;
                  var total_items = [];
                  var qty = frm.doc.quantity;
                  console.log(qty);
                  for (var i = 0; i < qty; i++) {
                    total_items.push(items_detailed[0]);
                  }

                  console.log(total_items);
                  for (var j = 0; j < total_items.length; j = j + 2) {
                    var group_string = "";
                    for (var g = 0; g < 2; g++) {
                      if (j + g < total_items.length) {
                        group_string +=
                          `\nBA3,` +
                          (4 + g * shift) +
                          `,8,1,2,63,0,0,` +
                          total_items[j + g]["code"] +
                          `\nAB,` +
                          (4 + g * shift) +
                          `,70,1,1,0,0E,` +
                          total_items[j + g]["code"] +
                          `\nAA,` +
                          (4 + g * shift) +
                          `,104,1,1,0,0E,` +
                          total_items[j + g]["name"] +
                          `\nAC,` +
                          (4 + g * shift) +
                          `,131,1,1,0,0E,Rs.` +
                          total_items[j + g]["rate"];
                      }
                    }
                    print_data.push(
                      frm.events.get_EZPL_string(frm, group_string)
                    );
                  }
                  return qz.print(config, print_data);
                },
                error: (r) => {
                  // on error
                },
              });
            })
            .then(frappe.ui.form.qz_success)
            .catch((err) => {
              frappe.ui.form.qz_fail(err);
            });
          // frm.events.on_success(frm);
        } else {
          frappe.throw("Fields for printing Item Labels are not available.");
        }

        //perform desired action such as routing to new form or fetching etc.
      },
      __("Utilities")
    );
    frm.add_custom_button(
      __("General Print"),
      async function () {
        if (
          frm.doc.general_item_code &&
          frm.doc.general_print_quantity &&
          frm.doc.general_print_date
        ) {
          console.log(frm.doc.general_item_code);
          frappe.ui.form
            .qz_connect()
            .then(function () {
              var printer = ""
              if (frm.doc.printer_name == "" || frm.doc.printer_name == null) {
                  printer = "Godex G500"
              }
              else {
                  printer = frm.doc.printer_name
                  .trim() 
                  .replace(/\s+/g, " ");
              }
              

            var config = qz.configs.create(printer); // Exact printer name from OS
              var print_data = [];
              var shift = 310;
              frappe.call({
                method:
                  "hkm.erpnext___custom.godex_print.validate_items",
                args: {
                  items: [frm.doc.general_item_code],
                },

                freeze: true,
                callback: (r) => {
                  console.log(r.message);
                  var items_detailed = r.message;
                  var total_items = [];
                  var qty = frm.doc.general_print_quantity;
                  for (var i = 0; i < qty; i++) {
                    total_items.push(items_detailed[0]);
                  }

                  var date = new Date(frm.doc.general_print_date);
                  var formattedDate = `${date.getDate().toString().padStart(2, '0')}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getFullYear()}`;


                  for (var j = 0; j < total_items.length; j = j + 2) {
                    var group_string = "";
                    for (var g = 0; g < 2; g++) {
                      if (j + g < total_items.length) {
                        group_string +=
                          `\nBA3,` +
                          (8 + g * shift) +
                          `,8,1,2,63,0,0,` +
                          total_items[j + g]["code"] +
                          `\nAB,` +
                          (4 + g * shift) +
                          `,70,1,1,0,0E,` +
                          total_items[j + g]["code"] +
                          `\nAA,` +
                          (4 + g * shift) +
                          `,104,1,1,0,0E,` +
                          total_items[j + g]["name"] +
                          `\nAC,` +
                          (4 + g * shift) +
                          `,130,1,1,0,0E,` +
                          formattedDate;
                      }
                    }
                    print_data.push(
                      frm.events.get_EZPL_string(frm, group_string)
                    );
                  }
                  return qz.print(config, print_data);
                },
                error: (r) => {
                  // on error
                },
              });
            })
            .then(frappe.ui.form.qz_success)
            .catch((err) => {
              frappe.ui.form.qz_fail(err);
            });
          // frm.events.on_success(frm);
        } else {
          frappe.throw("Fields for printing Item Labels are not available.");
        }

        //perform desired action such as routing to new form or fetching etc.
      },
      __("Utilities")
    );
    frm.add_custom_button(
      __("Print Old Stock"),
      async function () {
        if (
          frm.doc.old_stock_item_code &&
          frm.doc.old_stock_print_quantity
        ) {
          console.log(frm.doc.general_item_code);
          frappe.ui.form
            .qz_connect()
            .then(function () {
              var printer = ""
              if (frm.doc.printer_name == "" || frm.doc.printer_name == null) {
                  printer = "Godex G500"
              }
              else {
                  printer = frm.doc.printer_name
                  .trim() 
                  .replace(/\s+/g, " ");
              }
              

            var config = qz.configs.create(printer); // Exact printer name from OS
              var print_data = [];
              var shift = 310;
              frappe.call({
                method:
                  "hkm.erpnext___custom.godex_print.validate_items",
                args: {
                  items: [frm.doc.old_stock_item_code],
                },

                freeze: true,
                callback: (r) => {
                  console.log(r.message);
                  var items_detailed = r.message;
                  var total_items = [];
                  var qty = frm.doc.old_stock_print_quantity;
                  for (var i = 0; i < qty; i++) {
                    total_items.push(items_detailed[0]);
                  }

                  
                  for (var j = 0; j < total_items.length; j = j + 2) {
                    var group_string = "";
                    for (var g = 0; g < 2; g++) {
                      if (j + g < total_items.length) {
                        group_string +=
                          `\nBA3,` +
                          (8 + g * shift) +
                          `,8,1,2,63,0,0,` +
                          total_items[j + g]["code"] +
                          `\nAB,` +
                          (4 + g * shift) +
                          `,70,1,1,0,0E,` +
                          total_items[j + g]["code"] +
                          `\nAA,` +
                          (4 + g * shift) +
                          `,104,1,1,0,0E,` +
                          total_items[j + g]["name"] +
                          `\nAC,` +
                          (4 + g * shift) +
                          `,130,1,1,0,0E,` +
                          "";
                      }
                    }
                    print_data.push(
                      frm.events.get_EZPL_string(frm, group_string)
                    );
                  }
                  return qz.print(config, print_data);
                },
                error: (r) => {
                  // on error
                },
              });
            })
            .then(frappe.ui.form.qz_success)
            .catch((err) => {
              frappe.ui.form.qz_fail(err);
            });
          // frm.events.on_success(frm);
        } else {
          frappe.throw("Fields for printing Item Labels are not available.");
        }

        //perform desired action such as routing to new form or fetching etc.
      },
      __("Utilities")
    );
    frm.add_custom_button(
      __("Print Dates"),
      function () {
        if (frm.doc.date && frm.doc.quantity_date) {
          frappe.ui.form
            .qz_connect()
            .then(function () {
              var printer = ""
              if (frm.doc.printer_name == "" || frm.doc.printer_name == null) {
                  printer = "Godex G500"
              }
              else {
                  printer = frm.doc.printer_name
                  .trim() 
                  .replace(/\s+/g, " ");
              }
              

            var config = qz.configs.create(printer); // Exact printer name from OS
              var print_data = [];
              var shift = 310;
              for (var j = 0; j < frm.doc.quantity_date; j = j + 2) {
                var group_string = "";
                for (var g = 0; g < 2; g++) {
                  if (j + g < frm.doc.quantity_date) {
                    group_string +=
                      `\nAB,` +
                      (4 + g * shift) +
                      `,50,2,2,0,0E,` +
                      frappe.format(frm.doc.date, { fieldtype: "Date" });
                  }
                }
                print_data.push(frm.events.get_EZPL_string(frm, group_string));
              }
              return qz.print(config, print_data);
            })
            .then(frappe.ui.form.qz_success)
            .catch((err) => {
              frappe.ui.form.qz_fail(err);
            });
          // frm.events.on_success(frm)
        } else {
          frappe.throw("Fields for printing Date Labels are not available.");
        }
      },
      __("Utilities")
    );
  },

  on_success: function (frm) {
    frm.set_value("item_code", null);
    frm.set_value("quantity", null);
    frm.save();
  },
  get_EZPL_string: function (frm, data) {
    // Please refer to documentation for seetings : https://www.godexprinters.co.uk/downloads/manuals/desktop/EZPL_EN_J_20180226.pdf
    var settings = `
                        ^Q23,3
                        ^W76
                        ^H10
                        ^P1
                        ^S2
                        ^AD
                        ^C1
                        ^R8
                        ~Q+8
                        ^O0
                        ^D0
                        ^E18
                        ~R255
                        ^L
                        `;
    var end = `\nE`;
    var str = settings + data + end;
    var arr_data = str.split("\n");
    var final_data = "";
    for (var index in arr_data) {
      final_data += arr_data[index].trim() + "\x0D";
    }
    return final_data;
  },
});
function formatDateToDMY(date) {
  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
  });
}
function addDaysToDate(date, daysToAdd) {
  let newDate = new Date(date); // Clone the original date
  newDate.setDate(newDate.getDate() + daysToAdd);
  return newDate;
}

function getgroupString(itemCode, mfg, expiry, xOffset, yOffset) {
  if (itemCode.length <= 22) {
    let group_string = "";

    group_string = `^FO${xOffset},${
      yOffset + 5 + 50
    }^FB280,3,5,L^A0N,30,20 ^FD${itemCode}\n${"MFG:" + mfg}\n${
      "EXP:" + expiry
    }^FS`;

    const fontHeight = 30; // Adjust as needed
    const fontWidth = 20; // Adjust as needed
    const lineSpacing = 40; // Adjust line spacing for better visibility

    group_string = `
^FO${xOffset},${
      yOffset + 5 + 50
    }^FB280,3,${lineSpacing},L^A0N,${fontHeight},${fontWidth} 
^FD${itemCode}^FS
^FO${xOffset},${
      yOffset + 5 + 50 + 1.1 * lineSpacing
    }^A0N,${fontHeight},${fontWidth}^FDMFG:${mfg}^FS
^FO${xOffset},${
      yOffset + 5 + 50 + 2 * lineSpacing
    }^A0N,${fontHeight},${fontWidth}^FDEXP:${expiry}^FS
`;

    return group_string;
  }
  if (itemCode.length > 23 && itemCode.length <= 52) {
    const [part1, part2] = divideStringIntoTwoParts(itemCode);

    let group_string = "";

    const fontHeight = 30; // Adjust as needed
    const fontWidth = 20; // Adjust as needed
    const lineSpacing = 40; // Adjust line spacing for better visibility

    group_string = `
^FO${xOffset},${
      yOffset + 5 + 50
    }^FB280,3,${lineSpacing},L^A0N,${fontHeight},${fontWidth} 
^FD${part1}^FS
^FO${xOffset},${
      yOffset + 5 + 50 + lineSpacing
    }^A0N,${fontHeight},${fontWidth}^FD${part2}^FS
^FO${xOffset},${
      yOffset + 5 + 50 + 2 * lineSpacing
    }^A0N,${fontHeight},${fontWidth}^FDMFG:${mfg}^FS
^FO${xOffset},${
      yOffset + 5 + 50 + 3 * lineSpacing
    }^A0N,${fontHeight},${fontWidth}^FDEXP:${expiry}^FS
`;

    return group_string;
  }

  if (itemCode.length >= 53) {
    const [part1, part2, part3] = divideStringByWordsIntoThreeParts(itemCode);

    let group_string = "";

    const fontHeight = 30; // Adjust as needed
    const fontWidth = 20; // Adjust as needed
    const lineSpacing = 40; // Adjust line spacing for better visibility

    group_string = `
^FO${xOffset},${
      yOffset + 5 + 42
    }^FB280,3,${lineSpacing},L^A0N,${fontHeight},${fontWidth} 
^FD${part1}^FS
^FO${xOffset},${
      yOffset + 5 + 42 + lineSpacing
    }^A0N,${fontHeight},${fontWidth}^FD${part2}^FS
^FO${xOffset},${
      yOffset + 5 + 42 + 2 * lineSpacing
    }^A0N,${fontHeight},${fontWidth}^FD${part3}^FS
^FO${xOffset},${
      yOffset + 5 + 42 + 3 * lineSpacing
    }^A0N,${fontHeight},${fontWidth}^FDMFG:${mfg}^FS
^FO${xOffset},${
      yOffset + 5 + 42 + 4 * lineSpacing
    }^A0N,${fontHeight},${fontWidth}^FDEXP:${expiry}^FS
`;
    return group_string;
  }
}

function divideStringIntoTwoParts(inputString) {
  const midpoint = Math.floor(inputString.length / 2); // Approximate midpoint
  let splitPoint = midpoint;

  // Find the nearest space to the left of the midpoint
  while (splitPoint > 0 && inputString[splitPoint] !== " ") {
    splitPoint--;
  }

  // If no space is found to the left, find the nearest space to the right
  if (splitPoint === 0) {
    splitPoint = midpoint;
    while (splitPoint < inputString.length && inputString[splitPoint] !== " ") {
      splitPoint++;
    }
  }

  const part1 = inputString.substring(0, splitPoint).trim(); // Trim to remove extra spaces
  const part2 = inputString.substring(splitPoint).trim();

  return [part1, part2];
}

function divideStringByWordsIntoThreeParts(inputString) {
  const length = inputString.length;

  // Approximate split points
  const firstSplit = Math.floor(length / 3);
  const secondSplit = Math.floor((2 * length) / 3);

  // Adjust the first split point to the nearest space
  let firstSplitPoint = firstSplit;
  while (firstSplitPoint > 0 && inputString[firstSplitPoint] !== " ") {
    firstSplitPoint--;
  }

  // Adjust the second split point to the nearest space
  let secondSplitPoint = secondSplit;
  while (
    secondSplitPoint > firstSplitPoint &&
    inputString[secondSplitPoint] !== " "
  ) {
    secondSplitPoint--;
  }

  // If no space is found, search to the right
  if (firstSplitPoint === 0) {
    firstSplitPoint = firstSplit;
    while (firstSplitPoint < length && inputString[firstSplitPoint] !== " ") {
      firstSplitPoint++;
    }
  }

  if (secondSplitPoint <= firstSplitPoint) {
    secondSplitPoint = secondSplit;
    while (secondSplitPoint < length && inputString[secondSplitPoint] !== " ") {
      secondSplitPoint++;
    }
  }

  // Extract the three parts
  const part1 = inputString.substring(0, firstSplitPoint).trim();
  const part2 = inputString.substring(firstSplitPoint, secondSplitPoint).trim();
  const part3 = inputString.substring(secondSplitPoint).trim();

  return [part1, part2, part3];
}
