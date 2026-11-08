import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "../components"

Item {
    id: page
    objectName: "imageAnalysisPage"
    property var viewModel
    property var theme

    FileDialog {
        id: imagePicker
        title: "Select an image"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Image files (*.png *.jpg *.jpeg)"]
        onAccepted: page.viewModel.setSelectedImage(selectedFile.toString())
    }

    ScrollView {
        anchors.fill: parent
        clip: true
        leftPadding: 34
        rightPadding: 34
        topPadding: 30
        bottomPadding: 30
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: 20

            PageHeader {
                theme: page.theme
                eyebrow: "INPUT / IMAGE INSPECTION"
                title: "Inspect an image before analysis."
                description: "Choose a local image to compare its original appearance with the Digits-compatible 8 x 8 representation."
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.minimumHeight: 410
                spacing: 14

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: 420
                    radius: 6
                    color: page.theme.surface
                    border.color: page.theme.line

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 12

                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                Layout.fillWidth: true
                                text: page.viewModel.hasSelectedImage ? page.viewModel.selectedImageName : "IMAGE PREVIEW"
                                color: page.theme.ink
                                font.family: "Bahnschrift"
                                font.pixelSize: 11
                                font.weight: Font.Bold
                                elide: Text.ElideMiddle
                            }
                            Button {
                                id: chooseImageButton
                                text: "Choose image"
                                onClicked: imagePicker.open()
                                contentItem: Text {
                                    text: chooseImageButton.text
                                    color: "#FFFFFF"
                                    font.family: "Bahnschrift"
                                    font.pixelSize: 10
                                    font.weight: Font.DemiBold
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle { radius: 4; color: chooseImageButton.hovered ? "#A94A35" : page.theme.accent }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: 10

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 7
                                Text {
                                    text: "ORIGINAL"
                                    color: page.theme.muted
                                    font.family: "Bahnschrift"
                                    font.pixelSize: 8
                                    font.weight: Font.Bold
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    color: "#F0F3EF"
                                    radius: 4
                                    clip: true
                                    Image {
                                        id: originalImagePreview
                                        anchors.fill: parent
                                        anchors.margins: 10
                                        source: page.viewModel.selectedImageUrl
                                        fillMode: Image.PreserveAspectFit
                                        asynchronous: true
                                        visible: page.viewModel.hasSelectedImage && status === Image.Ready
                                    }
                                    Text {
                                        anchors.centerIn: parent
                                        width: parent.width - 24
                                        text: page.viewModel.processingError || "Select a PNG or JPEG image to begin."
                                        color: page.viewModel.processingError ? page.theme.accent : page.theme.muted
                                        font.family: "Segoe UI"
                                        font.pixelSize: 11
                                        horizontalAlignment: Text.AlignHCenter
                                        wrapMode: Text.WordWrap
                                        visible: !page.viewModel.hasSelectedImage || originalImagePreview.status === Image.Error
                                    }
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 7
                                Text {
                                    text: "8 x 8 / SCALED TO 0-16"
                                    color: page.theme.muted
                                    font.family: "Bahnschrift"
                                    font.pixelSize: 8
                                    font.weight: Font.Bold
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    color: "#F0F3EF"
                                    radius: 4
                                    clip: true
                                    Image {
                                        id: processedImagePreview
                                        anchors.fill: parent
                                        anchors.margins: 10
                                        source: page.viewModel.processedImageUrl
                                        fillMode: Image.PreserveAspectFit
                                        smooth: false
                                        visible: page.viewModel.hasProcessedImage && status === Image.Ready
                                    }
                                    Text {
                                        anchors.centerIn: parent
                                        width: parent.width - 24
                                        text: page.viewModel.processingError || "The processed 8 x 8 image will appear here."
                                        color: page.viewModel.processingError ? page.theme.accent : page.theme.muted
                                        font.family: "Segoe UI"
                                        font.pixelSize: 11
                                        horizontalAlignment: Text.AlignHCenter
                                        wrapMode: Text.WordWrap
                                        visible: !page.viewModel.hasProcessedImage || processedImagePreview.status === Image.Error
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 290
                    Layout.fillHeight: true
                    radius: 6
                    color: page.theme.surface
                    border.color: page.theme.line

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 14

                        Text {
                            text: "INSPECTION"
                            color: page.theme.green
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.weight: Font.Bold
                        }

                        Text {
                            Layout.fillWidth: true
                                text: page.viewModel.processingError
                                    ? "Image could not be processed"
                                    : page.viewModel.hasProcessedImage ? "Image processed" : "Waiting for input"
                            color: page.theme.ink
                            font.family: "Bahnschrift"
                            font.pixelSize: 18
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }

                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: page.theme.line }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            Text { text: "FILE NAME"; color: page.theme.muted; font.family: "Bahnschrift"; font.pixelSize: 8; font.weight: Font.Bold }
                            Text {
                                Layout.fillWidth: true
                                text: page.viewModel.hasSelectedImage ? page.viewModel.selectedImageName : "Not available"
                                color: page.theme.ink
                                font.family: "Segoe UI"
                                font.pixelSize: 11
                                wrapMode: Text.WrapAnywhere
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            Text { text: "IMAGE DIMENSIONS"; color: page.theme.muted; font.family: "Bahnschrift"; font.pixelSize: 8; font.weight: Font.Bold }
                            Text {
                                  text: page.viewModel.hasProcessedImage
                                      ? page.viewModel.originalImageWidth + " x " + page.viewModel.originalImageHeight + " px"
                                      : "Not available"
                                color: page.theme.ink
                                font.family: "Segoe UI"
                                font.pixelSize: 11
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: page.theme.line
                        }

                        EmptyState {
                            Layout.fillWidth: true
                            theme: page.theme
                            marker: "FX"
                                title: page.viewModel.hasProcessedImage
                                   ? page.viewModel.featureVectorLength + "-dimensional feature vector"
                                   : "No feature vector"
                                detail: page.viewModel.hasProcessedImage
                                    ? "Grayscale intensities are scaled to the Digits range of 0-16."
                                    : "A vector is produced after a supported image is selected."
                        }

                        Item { Layout.fillHeight: true }

                        Button {
                            id: clearImageButton
                            Layout.fillWidth: true
                            visible: page.viewModel.hasSelectedImage
                            text: "Clear image"
                            onClicked: page.viewModel.clearSelectedImage()
                            contentItem: Text {
                                text: clearImageButton.text
                                color: page.theme.ink
                                font.family: "Bahnschrift"
                                font.pixelSize: 10
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            background: Rectangle { radius: 4; color: "#F1F3EE"; border.color: page.theme.line }
                        }
                    }
                }
            }
        }
    }
}