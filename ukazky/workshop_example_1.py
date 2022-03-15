from qgis.core import (QgsProcessing, QgsFeatureSink, QgsProcessingException,
                       QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterNumber,
                       QgsProcessingFeedback, QgsProcessingContext, QgsGeometry, QgsFeature)


class WorkshopAlgorithm1(QgsProcessingAlgorithm):

    INPUT = "INPUT"
    BUFFER_SIZE = "BUFFERSIZE"
    OUTPUT = "OUTPUT"

    def createInstance(self):
        return WorkshopAlgorithm1()

    def name(self):
        return "workshop1"

    def displayName(self):
        return "Ukázka workshop 1"

    def group(self):
        return "Workshop GISOVA 2022"

    def groupId(self):
        return 'workshopgisova2022'

    def shortHelpString(self):
        return "Create buffer of given size around centroid and clip it to original geometry."

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT, "Input layer",
                                                [QgsProcessing.TypeVectorPolygon]))

        self.addParameter(
            QgsProcessingParameterNumber(self.BUFFER_SIZE,
                                         "Buffer size (in units of Input layer)",
                                         QgsProcessingParameterNumber.Double,
                                         defaultValue=1000,
                                         minValue=100,
                                         maxValue=10000))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, "Output layer"))

    def processAlgorithm(self, parameters, context: QgsProcessingContext,
                         feedback: QgsProcessingFeedback):

        source = self.parameterAsSource(parameters, self.INPUT, context)

        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, source.fields(),
                                               source.wkbType(), source.sourceCrs())

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

        return {self.OUTPUT: dest_id}
