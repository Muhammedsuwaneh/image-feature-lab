import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "../components"

Item {
    id: page
    objectName: "imageAnalysisPage"
    required property var viewModel
    required property var theme

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
                                        objectName: "originalImagePreview"
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
                                        objectName: "processedImagePreview"
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
                                    ? page.viewModel.preprocessingSummary
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

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: predictionColumn.implicitHeight + 40
                radius: 6
                color: page.theme.surface
                border.color: page.theme.line

                ColumnLayout {
                    id: predictionColumn
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 12
                    Text {
                        Layout.fillWidth: true
                        text: "EXPERIMENTAL k-NN / k = " + page.viewModel.knnK
                        color: page.theme.green
                        font.family: "Bahnschrift"
                        font.pixelSize: 11
                        font.weight: Font.Bold
                    }
                    Text {
                        objectName: "predictionText"
                        Layout.fillWidth: true
                        text: page.viewModel.knnPredictionError ? page.viewModel.knnPredictionError
                            : page.viewModel.datasetLoading ? "Loading the reference dataset..."
                            : !page.viewModel.hasDigitsDataset ? "Reference dataset unavailable: " + page.viewModel.datasetError
                            : page.viewModel.hasKnnPrediction ? "Predicted digit: " + page.viewModel.knnPredictedLabel
                            : "Choose an image to compare with the training samples."
                        color: page.theme.ink
                        font.pixelSize: 17
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        Layout.fillWidth: true
                        text: page.viewModel.knnEvaluationRunning ? "Evaluating the held-out baseline... You can already classify images and run experiments."
                            : page.viewModel.knnEvaluationError ? "Baseline evaluation failed: " + page.viewModel.knnEvaluationError
                            : page.viewModel.hasKnnEvaluation
                            ? "Held-out baseline accuracy: " + (page.viewModel.knnTestAccuracy * 100).toFixed(2) + "% | Uploads are normalized for stroke polarity, margins and placement. This is a research classifier."
                            : "The reference images contain 8 x 8 grayscale digit samples."
                        color: page.theme.muted
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 16
                        Repeater {
                            model: page.viewModel.knnNeighbors
                            ColumnLayout {
                                id: neighbor
                                required property var modelData
                                Layout.fillWidth: true
                                Image {
                                    objectName: "neighborImagePreview"
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 100
                                    source: neighbor.modelData.source
                                    fillMode: Image.PreserveAspectFit
                                    smooth: false
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: "Digit " + neighbor.modelData.label + " | sample " + neighbor.modelData.index
                                    color: page.theme.ink
                                    font.pixelSize: 11
                                    horizontalAlignment: Text.AlignHCenter
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: "Distance " + Number(neighbor.modelData.distance).toFixed(3)
                                    color: page.theme.muted
                                    font.pixelSize: 10
                                    horizontalAlignment: Text.AlignHCenter
                                }
                            }
                        }
                    }
                    TextArea {
                        Layout.fillWidth: true
                        visible: page.viewModel.hasProcessedImage
                        text: "64 image features: [" + page.viewModel.featureVector.join(", ") + "]"
                        readOnly: true
                        wrapMode: TextEdit.WordWrap
                        color: page.theme.ink
                        font.family: "Consolas"
                        font.pixelSize: 10
                    }
                }
            }
        }
    }
}
