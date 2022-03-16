from qgis.core import (QgsProcessing, QgsFeatureSink, QgsProcessingException,
                       QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink, QgsProcessingFeedback,
                       QgsProcessingContext, QgsGeometry, QgsFeature,
                       QgsProcessingParameterDistance, QgsProcessingUtils)


class WorkshopAlgorithm3(QgsProcessingAlgorithm):

    INPUT = "INPUT"
    BUFFER_SIZE = "BUFFERSIZE"
    OUTPUT = "OUTPUT"

    def createInstance(self):
        return WorkshopAlgorithm3()

    def name(self):
        return "workshop3"

    def displayName(self):
        return "Ukázka workshop 3"

    def group(self):
        return "Workshop GISOVA 2022"

    def groupId(self):
        return 'workshopgisova2022'

    def shortHelpString(self):

        help = [
            "Create buffer of given size around centroid and clip it to original geometry.",
            "Buffer size is considered as distance.",
            "Includes verification of input data, to only allow projected data.",
            "Buffer size must be bigger then 100."
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
