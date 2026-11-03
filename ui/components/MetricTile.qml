import QtQuick
import QtQuick.Layouts

Rectangle {
    id: metricTile
    property var theme
    property string label: ""
    property string value: ""
    property string detail: ""
    property color marker: "#C75D43"
    radius: 6
    color: theme.surface
    border.color: theme.line

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Rectangle {
                Layout.preferredWidth: 3
                Layout.preferredHeight: 13
                radius: 2
                color: metricTile.marker
            }
            Text {
                Layout.fillWidth: true
                text: metricTile.label
                color: metricTile.theme.muted
                font.family: "Bahnschrift"
                font.pixelSize: 10
                font.weight: Font.Bold
                elide: Text.ElideRight
            }
        }

        Text {
            Layout.fillWidth: true
            text: metricTile.value
            color: metricTile.theme.ink
            font.family: "Bahnschrift"
            font.pixelSize: 19
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        Text {
            Layout.fillWidth: true
            text: metricTile.detail
            color: metricTile.theme.muted
            font.family: "Segoe UI"
            font.pixelSize: 10
            wrapMode: Text.WordWrap
        }
    }
}