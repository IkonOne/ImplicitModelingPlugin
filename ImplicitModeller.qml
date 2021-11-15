import UM 1.1 as UM
import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1

UM.Dialog {
    id: base

    property alias implicitFunctionIndex: implicitFunctionCombo.currentIndex
    property alias periods: periods.text
    property alias lineCount: lineCount.text
    property alias lineWidth: lineWidth.text
    property alias dimensions: dimensions.text

    ColumnLayout {
        RowLayout {
            Label { text: "Implicit Surface Function" }
            ComboBox {
                id : implicitFunctionCombo
                model : ListModel {
                    ListElement { text: "Gyroid" }
                    ListElement { text: "Fisher Koch S" }
                }
            }
        }

        RowLayout {
            Label { text: "Periods" }
            TextField {
                id: periods
                text: "1.0"
                validator: DoubleValidator { decimals: 4; bottom: 0.0; top: 100.0 }
            }
        }

        RowLayout {
            Label { text: "Line Count"}
            TextField {
                id: lineCount
                text: "1"
                validator: IntValidator { bottom: 0; top: 10 }
            }
        }

        RowLayout {
            Label { text: "Line Width (mm)" }
            TextField {
                id: lineWidth
                text: "0.4"
                validator: DoubleValidator { decimals: 4; bottom: 0.0; top: 10000.0 }
            }
        }


        RowLayout {
            Label { text: "Dimensions (mm)" }
            TextField {
                id: dimensions
                text: "100"
                validator: DoubleValidator { decimals: 4; bottom: 0.0; top: 10000.0 }
            }
        }

        RowLayout {
            Button {
                text: "Accept"
                onClicked: base.accept()
            }

            Button {
                text: "Cancel"
                onClicked: base.reject()
            }
        }
    }
}