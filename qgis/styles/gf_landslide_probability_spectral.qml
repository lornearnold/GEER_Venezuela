<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34" styleCategories="Symbology">
  <pipe>
    <provider>
      <resampling zoomedInResamplingMethod="nearestNeighbour" zoomedOutResamplingMethod="nearestNeighbour" maxOversampling="2" enabled="false"/>
    </provider>
    <rasterrenderer type="singlebandpseudocolor" opacity="0.55" band="1" alphaBand="-1" classificationMin="0" classificationMax="0.21" nodataColor="">
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader colorRampType="INTERPOLATED" classificationMode="1" clip="0" labelPrecision="4" minimumValue="0" maximumValue="0.21">
          <item value="0" color="#7472b8" label="0 (no modeled failure)" alpha="255"/>
          <item value="0.002" color="#52b062" label="0.002" alpha="255"/>
          <item value="0.008" color="#a6d96a" label="0.008" alpha="255"/>
          <item value="0.015" color="#ffffbf" label="0.015" alpha="255"/>
          <item value="0.03" color="#fee08b" label="0.03" alpha="255"/>
          <item value="0.06" color="#fdae61" label="0.06" alpha="255"/>
          <item value="0.12" color="#d95f4b" label="0.12" alpha="255"/>
          <item value="0.21" color="#9e3a26" label="0.21" alpha="255"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0" gamma="1"/>
    <huesaturation saturation="0" grayscaleMode="0" colorizeOn="0" colorizeRed="255" colorizeGreen="128" colorizeBlue="128" colorizeStrength="100" invertColors="0"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
