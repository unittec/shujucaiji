/*
This is a UI file (.ui.qml) that is intended to be edited in Qt Design Studio only.
It is supposed to be strictly declarative and only uses a subset of QML. If you edit
this file manually, you might introduce QML code that is not supported by Qt Design Studio.
Check out https://doc.qt.io/qtcreator/creator-quick-ui-forms.html for details on .ui.qml files.
*/

import QtQuick
import QtQuick.Controls
import QtCharts
import QtQuick.Window
import QtQuick.Layouts
import DataVisualization 1.0


ApplicationWindow {
    id: app
    width: 1024
    height: 576
    visible: true
    minimumWidth: 1024
    minimumHeight: 576
    color: '#ffffff'

    property bool _stop: false
//    onVisibilityChanged: {
//            if (Qt.application.active) {
//                console.log("Window is not minimized");
//                _stop = false
//            } else {
//                console.log("Window is minimized");
//                _stop = true
//            }
//        }

    DataVisualization {
        id: dataVisualization
    }

    function addSineWave(lineSeries, startX, endX, amplitude, frequency, phaseShift) {
        //LineSeries对象,开始X、结束X、振幅、频率、相位偏移
        var step = 0.2
        for (var x = startX; x <= endX; x += step) {
            var y = amplitude * Math.sin(2 * Math.PI * frequency * (x + phaseShift))
            lineSeries.append(x, y + amplitude)
        }
    }

    function reset(lineSeries, newList){
        if (app._stop)
            return
        lineSeries.clear()
        for (var i = 0; i < newList.length; ++i)
            lineSeries.append(i+1, newList[i])
    }


    Row {
        z: 99
        id: menu
        x: 10
        y: 10
        height: 30
        Button {
            width: 70
            height: 30
            text: "开始"
            onClicked: {
                dataVisualization.nid_start()
                dataVisualization.myo_start()
            }
        }
        Button {
            width: 70
            height: 30
            text: "停止"
            onClicked: {
                dataVisualization.nid_stop()
                dataVisualization.myo_stop()
            }
        }

        Button {
            width: 70
            height: 30
            text: "清除"
            onClicked: {
                l1.clear()
                l2.clear()
                l3.clear()
                l4.clear()
                l5.clear()
                miniChartView1_line.clear()
                miniChartView2_line.clear()
                miniChartView3_line.clear()
                miniChartView4_line.clear()
                miniChartView5_line.clear()
                miniChartView6_line.clear()
                miniChartView7_line.clear()
                miniChartView8_line.clear()
            }
        }
        Button {
            width: 70
            height: 30
            text: "保存"
        }
        Button {
            width: 70
            height: 30
            text: "控制打开"
            onClicked: dataVisualization.control_switch()
        }
    }
    Rectangle{
        id: centerBar
        x: parent.width / 2
        width: 1
        height: parent.height
        color: '#00000000'
        z: 99
        property real leftRatio: (x + 1) / parent.width
        property real rightRatio: (parent.width - (x + 1)) / parent.width
        MouseArea {
            height: parent.height
            width: 7
            anchors.centerIn: parent
            drag.target: parent
            drag.axis: Drag.XAxis
            hoverEnabled: true
            drag.onActiveChanged: {
                if (drag.active){
                    app._stop = true
                    cursorShape = Qt.SplitHCursor
                }
                else {
                    app._stop = false
                    cursorShape = Qt.ArrowCursor
                }
            }
            onEntered: cursorShape = Qt.SplitHCursor
            onExited: cursorShape = Qt.ArrowCursor
            onPressed: cursorShape = Qt.SplitHCursor
            onPressAndHold: cursorShape = Qt.SplitHCursor
            onReleased: cursorShape = Qt.ArrowCursor
            onPositionChanged: cursorShape = Qt.SplitHCursor
        }
    }

    Rectangle {
        width: parent.width * centerBar.leftRatio
        height: parent.height - menu.height - menu.y * 2
        y: menu.height + menu.y * 2
        border.color: '#00000000'
        clip: true


        ChartView {
            id: chartView1
            width: parent.width + 50
            height: parent.height + 50

            anchors.centerIn: parent
            legend.showToolTips: true
            legend.markerShape: Legend.MarkerShapeCircle
            antialiasing: true
            legend.enabled: true
            property real x_min: 0
            property real x_max: 50
            property real y_min: 0
            property real y_max: 5

            ValuesAxis { id: ax; min: chartView1.x_min; max: chartView1.x_max; labelFormat: "%.0f" }
            ValuesAxis { id: ay; min: chartView1.y_min; max: chartView1.y_max }

            LineSeries {
                id: l1
                name: "<font face='SimSun' size='3'>手指_0</font>"
                axisX: ax
                axisY: ay
                property list<var> pointList: dataVisualization.nid_data[0]
                onPointListChanged: reset(l1, pointList)

            }
            LineSeries {
                id: l2
                name: "<font face='SimSun' size='3'>手指_1</font>"
                property list<var> pointList: dataVisualization.nid_data[1]
                onPointListChanged: reset(l2, pointList)


            }
            LineSeries {
                id: l3
                name: "<font face='SimSun' size='3'>手指_2</font>"
                property list<var> pointList: dataVisualization.nid_data[2]
                onPointListChanged: reset(l3, pointList)
            }
            LineSeries {
                id: l4
                name: "<font face='SimSun' size='3'>手指_3</font>"
                property list<var> pointList: dataVisualization.nid_data[3]
                onPointListChanged: reset(l4, pointList)
            }
            LineSeries {
                id: l5
                name: "<font face='SimSun' size='3'>手指_4</font>"
                property list<var> pointList: dataVisualization.nid_data[4]
                onPointListChanged: reset(l5, pointList)
            }
        }

    }


    Rectangle {
        id: emgView
        width: parent.width * centerBar.rightRatio
        height: parent.height
        anchors.right: parent.right
        property int rowCount: 2
        property int columCount: 4
        property int chartViewWidth: Math.ceil(width / rowCount)
        property int chartViewHeight: Math.ceil(height / columCount)
        property real x_min: 0
        property real x_max: 50
        property real y_min: 0
        property real y_max: 10
        property int miniVerticalCenterOffset: 0
        property int miniHorizontalCenterOffset: -5
        property int miniWidthAdd: 50
        property int miniHeightAdd: 50
        property color lineColor: "darkturquoise"
        property color textColor: "black"
        property color miniColor: '#00000000'
        property color miniBorderColor: '#e2e2e2'
        property bool miniLegendVisble: false
        property real miniRadius: 0
        property real textOpacity: 0.2
        property var miniChartView1_line: miniChartView1_line
        property var miniChartView2_line: miniChartView2_line
        property var miniChartView3_line: miniChartView3_line
        property var miniChartView4_line: miniChartView4_line
        property var miniChartView5_line: miniChartView5_line
        property var miniChartView6_line: miniChartView6_line
        property var miniChartView7_line: miniChartView7_line
        property var miniChartView8_line: miniChartView8_line

        function add(){
            addSineWave(miniChartView1_line, 0, 50, 3, 0.2, 0)
            addSineWave(miniChartView2_line, 0, 50, 3, 0.2, 0)
            addSineWave(miniChartView3_line, 0, 50, 3, 0.2, 0)
            addSineWave(miniChartView4_line, 0, 50, 3, 0.2, 0)
            addSineWave(miniChartView5_line, 0, 50, 3, 0.2, 0)
            addSineWave(miniChartView6_line, 0, 50, 3, 0.2, 0)
            addSineWave(miniChartView7_line, 0, 50, 3, 0.2, 0)
            addSineWave(miniChartView8_line, 0, 50, 3, 0.2, 0)
        }


        Rectangle {
            width: parent.chartViewWidth; height: parent.chartViewHeight
            anchors.left: parent.left; anchors.top: parent.top
            border.color: emgView.miniBorderColor; radius: emgView.miniRadius
            clip: true
            Text {
                text: 'EMG_1'
                opacity: emgView.textOpacity; color: emgView.textColor
                font.bold: true; font.pixelSize: parent.height / 4
                anchors.fill: parent; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter
            }
            ChartView {
                id: miniChartView1
                width: parent.width + emgView.miniWidthAdd; height: parent.height + emgView.miniHeightAdd
                anchors.centerIn: parent; anchors.verticalCenterOffset: emgView.miniVerticalCenterOffset; anchors.horizontalCenterOffset: emgView.miniHorizontalCenterOffset
                legend.markerShape: Legend.MarkerShapeCircle; legend.visible: emgView.miniLegendVisble

                antialiasing: true; backgroundColor: emgView.miniColor

                LineSeries {
                    id: miniChartView1_line; color: emgView.lineColor
                    axisX: ValuesAxis {min: emgView.x_min; max: emgView.x_max; labelFormat: "%.0f" }
                    axisY: ValuesAxis {min: emgView.y_min; max: emgView.y_max }
                    property list<var> pointList: dataVisualization.emg_data[0]
                    onPointListChanged: reset(miniChartView1_line, pointList)
                }
            }
        }
        Rectangle {
            width: parent.chartViewWidth; height: parent.chartViewHeight
            anchors.right: parent.right
            anchors.top: parent.top
            border.color: emgView.miniBorderColor; radius: emgView.miniRadius
            clip: true
            Text {
                text: 'EMG_5'
                z: 2; opacity: emgView.textOpacity; color: emgView.textColor
                font.bold: true; font.pixelSize: parent.height / 4
                anchors.fill: parent; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter
            }
            ChartView {
                id: miniChartView5
                width: parent.width + emgView.miniWidthAdd; height: parent.height + emgView.miniHeightAdd
                anchors.centerIn: parent; anchors.verticalCenterOffset: emgView.miniVerticalCenterOffset; anchors.horizontalCenterOffset: emgView.miniHorizontalCenterOffset
                legend.markerShape: Legend.MarkerShapeCircle; legend.visible: emgView.miniLegendVisble
                antialiasing: true; backgroundColor: emgView.miniColor
                LineSeries {
                    id: miniChartView5_line; color: emgView.lineColor
                    axisX: ValuesAxis {min: emgView.x_min; max: emgView.x_max; labelFormat: "%.0f" }
                    axisY: ValuesAxis {min: emgView.y_min; max: emgView.y_max }
                    property list<var> pointList: dataVisualization.emg_data[4]
                    onPointListChanged: reset(miniChartView5_line, pointList)
                }
            }
        }
        Rectangle {
            width: parent.chartViewWidth; height: parent.chartViewHeight
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.topMargin: height
            border.color: emgView.miniBorderColor; radius: emgView.miniRadius
            clip: true
            Text {
                text: 'EMG_2'
                z: 2; opacity: emgView.textOpacity; color: emgView.textColor
                font.bold: true; font.pixelSize: parent.height / 4
                anchors.fill: parent; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter
            }
            ChartView {
                id: miniChartView2
                width: parent.width + emgView.miniWidthAdd; height: parent.height + emgView.miniHeightAdd
                anchors.centerIn: parent; anchors.verticalCenterOffset: emgView.miniVerticalCenterOffset; anchors.horizontalCenterOffset: emgView.miniHorizontalCenterOffset
                legend.markerShape: Legend.MarkerShapeCircle; legend.visible: emgView.miniLegendVisble
                antialiasing: true; backgroundColor: emgView.miniColor
                LineSeries {
                    id: miniChartView2_line; color: emgView.lineColor
                    axisX: ValuesAxis {min: emgView.x_min; max: emgView.x_max; labelFormat: "%.0f" }
                    axisY: ValuesAxis {min: emgView.y_min; max: emgView.y_max }
                    property list<var> pointList: dataVisualization.emg_data[1]
                    onPointListChanged: reset(miniChartView2_line, pointList)
                }
            }
        }
        Rectangle {
            width: parent.chartViewWidth; height: parent.chartViewHeight
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.topMargin: height
            border.color: emgView.miniBorderColor; radius: emgView.miniRadius
            clip: true
            Text {
                text: 'EMG_6'
                z: 2; opacity: emgView.textOpacity; color: emgView.textColor
                font.bold: true; font.pixelSize: parent.height / 4
                anchors.fill: parent; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter
            }
            ChartView {
                id: miniChartView6
                width: parent.width + emgView.miniWidthAdd; height: parent.height + emgView.miniHeightAdd
                anchors.centerIn: parent; anchors.verticalCenterOffset: emgView.miniVerticalCenterOffset; anchors.horizontalCenterOffset: emgView.miniHorizontalCenterOffset
                legend.markerShape: Legend.MarkerShapeCircle; legend.visible: emgView.miniLegendVisble
                antialiasing: true; backgroundColor: emgView.miniColor
                LineSeries {
                    id: miniChartView6_line; color: emgView.lineColor
                    axisX: ValuesAxis {min: emgView.x_min; max: emgView.x_max; labelFormat: "%.0f" }
                    axisY: ValuesAxis {min: emgView.y_min; max: emgView.y_max }
                    property list<var> pointList: dataVisualization.emg_data[5]
                    onPointListChanged: reset(miniChartView6_line, pointList)
                }
            }
        }
        Rectangle {
            width: parent.chartViewWidth; height: parent.chartViewHeight
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            anchors.bottomMargin: height
            border.color: emgView.miniBorderColor; radius: emgView.miniRadius
            clip: true
            Text {
                text: 'EMG_3'
                z: 2; opacity: emgView.textOpacity; color: emgView.textColor
                font.bold: true; font.pixelSize: parent.height / 4
                anchors.fill: parent; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter
            }
            ChartView {
                id: miniChartView3
                width: parent.width + emgView.miniWidthAdd; height: parent.height + emgView.miniHeightAdd
                anchors.centerIn: parent; anchors.verticalCenterOffset: emgView.miniVerticalCenterOffset; anchors.horizontalCenterOffset: emgView.miniHorizontalCenterOffset
                legend.markerShape: Legend.MarkerShapeCircle; legend.visible: emgView.miniLegendVisble
                antialiasing: true; backgroundColor: emgView.miniColor
                LineSeries {
                    id: miniChartView3_line; color: emgView.lineColor
                    axisX: ValuesAxis {min: emgView.x_min; max: emgView.x_max; labelFormat: "%.0f" }
                    axisY: ValuesAxis {min: emgView.y_min; max: emgView.y_max }
                    property list<var> pointList: dataVisualization.emg_data[2]
                    onPointListChanged: reset(miniChartView3_line, pointList)
                }
            }
        }
        Rectangle {
            width: parent.chartViewWidth; height: parent.chartViewHeight
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.bottomMargin: height
            border.color: emgView.miniBorderColor; radius: emgView.miniRadius
            clip: true
            Text {
                text: 'EMG_7'
                z: 2; opacity: emgView.textOpacity; color: emgView.textColor
                font.bold: true; font.pixelSize: parent.height / 4
                anchors.fill: parent; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter
            }
            ChartView {
                id: miniChartView7
                width: parent.width + emgView.miniWidthAdd; height: parent.height + emgView.miniHeightAdd
                anchors.centerIn: parent; anchors.verticalCenterOffset: emgView.miniVerticalCenterOffset; anchors.horizontalCenterOffset: emgView.miniHorizontalCenterOffset
                legend.markerShape: Legend.MarkerShapeCircle; legend.visible: emgView.miniLegendVisble
                antialiasing: true; backgroundColor: emgView.miniColor
                LineSeries {
                    id: miniChartView7_line; color: emgView.lineColor
                    axisX: ValuesAxis {min: emgView.x_min; max: emgView.x_max; labelFormat: "%.0f" }
                    axisY: ValuesAxis {min: emgView.y_min; max: emgView.y_max }
                    property list<var> pointList: dataVisualization.emg_data[6]
                    onPointListChanged: reset(miniChartView7_line, pointList)
                }
            }
        }
        Rectangle {
            width: parent.chartViewWidth; height: parent.chartViewHeight
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            border.color: emgView.miniBorderColor; radius: emgView.miniRadius
            clip: true
            Text {
                text: 'EMG_4'
                z: 2; opacity: emgView.textOpacity; color: emgView.textColor
                font.bold: true; font.pixelSize: parent.height / 4
                anchors.fill: parent; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter
            }
            ChartView {
                id: miniChartView4
                width: parent.width + emgView.miniWidthAdd; height: parent.height + emgView.miniHeightAdd
                anchors.centerIn: parent; anchors.verticalCenterOffset: emgView.miniVerticalCenterOffset; anchors.horizontalCenterOffset: emgView.miniHorizontalCenterOffset
                legend.markerShape: Legend.MarkerShapeCircle; legend.visible: emgView.miniLegendVisble
                antialiasing: true; backgroundColor: emgView.miniColor
                LineSeries {
                    id: miniChartView4_line; color: emgView.lineColor
                    axisX: ValuesAxis {min: emgView.x_min; max: emgView.x_max; labelFormat: "%.0f" }
                    axisY: ValuesAxis {min: emgView.y_min; max: emgView.y_max }
                    property list<var> pointList: dataVisualization.emg_data[3]
                    onPointListChanged: reset(miniChartView4_line, pointList)
                }
            }
        }
        Rectangle {
            width: parent.chartViewWidth; height: parent.chartViewHeight
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            border.color: emgView.miniBorderColor; radius: emgView.miniRadius
            clip: true
            Text {
                text: 'EMG_8'
                z: 2; opacity: emgView.textOpacity; color: emgView.textColor
                font.bold: true; font.pixelSize: parent.height / 4
                anchors.fill: parent; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter
            }
            ChartView {
                id: miniChartView8
                width: parent.width + emgView.miniWidthAdd; height: parent.height + emgView.miniHeightAdd
                anchors.centerIn: parent; anchors.verticalCenterOffset: emgView.miniVerticalCenterOffset; anchors.horizontalCenterOffset: emgView.miniHorizontalCenterOffset
                legend.markerShape: Legend.MarkerShapeCircle; legend.visible: emgView.miniLegendVisble
                antialiasing: true; backgroundColor: emgView.miniColor
                LineSeries {
                    name: '123'
                    id: miniChartView8_line; color: emgView.lineColor
                    axisX: ValuesAxis {min: emgView.x_min; max: emgView.x_max; labelFormat: "%.0f" }
                    axisY: ValuesAxis {min: emgView.y_min; max: emgView.y_max }
                    property list<var> pointList: dataVisualization.emg_data[7]
                    onPointListChanged: reset(miniChartView8_line, pointList)
                }
            }
        }


    }
}




