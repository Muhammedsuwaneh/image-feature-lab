import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: pageHeader
    property var theme
    property string eyebrow: ""
    property string title: ""
    property string description: ""
    spacing: 7

    Text {
        text: pageHeader.eyebrow
        color: pageHeader.theme.green
        font.family: "Bahnschrift"
        font.pixelSize: 9
        font.weight: Font.Bold
    }
    Text {
        Layout.fillWidth: true
        text: pageHeader.title
        color: pageHeader.theme.ink
        font.family: "Bahnschrift"
        font.pixelSize: 28
        font.weight: Font.DemiBold
        wrapMode: Text.WordWrap
    }
    Text {
        Layout.fillWidth: true
        text: pageHeader.description
        color: pageHeader.theme.muted
        font.family: "Segoe UI"
        font.pixelSize: 13
        wrapMode: Text.WordWrap
    }
}