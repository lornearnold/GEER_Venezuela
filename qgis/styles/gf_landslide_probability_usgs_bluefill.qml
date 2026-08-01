<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34" styleCategories="Symbology">
  <pipe>
    <provider>
      <resampling zoomedInResamplingMethod="nearestNeighbour" zoomedOutResamplingMethod="nearestNeighbour" maxOversampling="2" enabled="false"/>
    </provider>
    <rasterrenderer type="singlebandpseudocolor" opacity="0.75" band="1" alphaBand="-1" classificationMin="0" classificationMax="0.4" nodataColor="">
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader colorRampType="INTERPOLATED" classificationMode="1" clip="0" labelPrecision="6" minimumValue="0" maximumValue="0.4">
          <item value="0" color="#7472b8" label="0" alpha="255"/>
          <item value="0.02" color="#7472b8" label="&lt;2%" alpha="255"/>
          <item value="0.021" color="#ffffb2" label="2%" alpha="255"/>
          <item value="0.05" color="#fecc5c" label="5%" alpha="255"/>
          <item value="0.1" color="#fd8d3c" label="10%" alpha="255"/>
          <item value="0.2" color="#f03b20" label="20%" alpha="255"/>
          <item value="0.4" color="#bd0026" label="&gt;=40%" alpha="255"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0" gamma="1"/>
    <huesaturation saturation="0" grayscaleMode="0" colorizeOn="0" colorizeRed="255" colorizeGreen="128" colorizeBlue="128" colorizeStrength="100" invertColors="0"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
