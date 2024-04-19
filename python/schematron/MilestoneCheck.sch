<schema xmlns:sch="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2"
    xmlns:sqf="http://www.schematron-quickfix.com/validator/process"
    xmlns="http://purl.oclc.org/dsdl/schematron">
    <pattern name="Milestone checks">
        <rule context="ms[@style='qt-s']">
            <assert test="following::ms[@style='qt-s' or @style='qt-e'][1]/@style = 'qt-e'">Milestone start missing end</assert>
        </rule>
        <rule context="ms[@style='qt-e']">
            <assert test="preceding::ms[@style='qt-s' or @style='qt-e'][1]/@style = 'qt-s'">Milestone end missing start</assert>
        </rule>
    </pattern>
</schema>