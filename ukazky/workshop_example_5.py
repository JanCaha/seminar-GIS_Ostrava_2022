from qgis.core import (QgsProcessing, QgsFeatureSink, QgsProcessingException,
                       QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink, QgsProcessingFeedback,
                       QgsProcessingContext, QgsGeometry, QgsFeature,
                       QgsProcessingParameterDistance, QgsProcessingUtils,
                       QgsProcessingOutputNumber, QgsGradientColorRamp, QgsVectorLayer, QgsField,
                       QgsGraduatedSymbolRenderer, QgsClassificationJenks)

from qgis.PyQt.QtCore import (QVariant)
from qgis.PyQt.QtGui import (QColor)


class WorkshopAlgorithm5(QgsProcessingAlgorithm):

    INPUT = "INPUT"
    BUFFER_SIZE = "BUFFERSIZE"
    OUTPUT = "OUTPUT"
    FEATURE_COUNT = "FEATURECOUNT"

    def createInstance(self):
        return WorkshopAlgorithm5()

    def name(self):
        return "workshop5"

    def displayName(self):
        return "Ukázka workshop 5"

    def group(self):
        return "Workshop GISOVA 2022"

    def groupId(self):
        return 'workshopgisova2022'

    def shortHelpString(self):

        help = [
            "Create buffer of given size around centroid and clip it to original geometry.",
            "Buffer size is considered as distance.",
            "Includes verification of input data, to only allow projected data.",
            "Buffer size must be bigger then 100.", "Output is rendedred using specific renderer."
        ]

        help = "<br/><br/>".join(help)

        help = {"ALG_DESC": help}

        help = QgsProcessingUtils.formatHelpMapAsHtml(help, self)

        return help

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT, "Input layer",
                                                [QgsProcessing.TypeVectorPolygon]))

        self.addParameter(
            QgsProcessingParameterDistance(self.BUFFER_SIZE,
                                           "Buffer size",
                                           parentParameterName=self.INPUT,
                                           defaultValue=10))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, "Output layer"))

        self.addOutput(QgsProcessingOutputNumber(self.FEATURE_COUNT, "Feature count"))

    def checkParameterValues(self, parameters, context: QgsProcessingContext):

        source = self.parameterAsSource(parameters, self.INPUT, context)

        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        if source.sourceCrs().isGeographic():
            return (False, "Data must be projected! Currently they are in geographic CRS.")

        buffer_size = self.parameterAsDouble(parameters, self.BUFFER_SIZE, context)

        if buffer_size < 100:
            return (
                False,
                "The buffer size is set to `{}` which is small number and would likely produce results without meaning, the value should be at least `100`."
                .format(buffer_size))

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context: QgsProcessingContext,
                         feedback: QgsProcessingFeedback):

        source = self.parameterAsSource(parameters, self.INPUT, context)

        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        (sink, self.dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                                    source.fields(), source.wkbType(),
                                                    source.sourceCrs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        buffer_size = self.parameterAsDouble(parameters, self.BUFFER_SIZE, context)

        feedback.pushInfo("Data loaded, output created. Processing features ...")

        total = 100.0 / source.featureCount() if source.featureCount() else 0

        features = source.getFeatures()

        for current, feature in enumerate(features):

            if feedback.isCanceled():
                break

            original_geom = feature.geometry()

            buffered_geom: QgsGeometry = original_geom.centroid().buffer(buffer_size, 5)

            clipped_geom = buffered_geom.intersection(original_geom)

            new_feature = QgsFeature(feature)

            new_feature.clearGeometry()

            new_feature.setGeometry(clipped_geom)

            sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

            feedback.setProgress(int(current * total))

        return {self.OUTPUT: self.dest_id, 
                self.FEATURE_COUNT: source.featureCount()}

    def postProcessAlgorithm(self, context: QgsProcessingContext, feedback: QgsProcessingFeedback):

        output_layer: QgsVectorLayer = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)

        field_name = "area"

        output_layer.addExpressionField("$area", QgsField(field_name, QVariant.Double))

        renderer = QgsGraduatedSymbolRenderer()
        renderer.setClassAttribute(field_name)
        renderer.setClassificationMethod(QgsClassificationJenks())
        renderer.setGraduatedMethod(QgsGraduatedSymbolRenderer.GraduatedColor)
        renderer.setSourceColorRamp(QgsGradientColorRamp(QColor(225, 225, 225), QColor(255, 0, 0)))
        renderer.updateClasses(output_layer, 5)

        output_layer.setRenderer(renderer)
        output_layer.triggerRepaint()

        return {self.OUTPUT: self.dest_id, 
                self.FEATURE_COUNT: source.featureCount()}}
