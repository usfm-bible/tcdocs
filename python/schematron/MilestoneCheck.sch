<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt1"
    xmlns:sqf="http://www.schematron-quickfix.com/validator/process"
    xmlns="http://purl.oclc.org/dsdl/schematron">
    <sch:pattern>
        <sch:rule context="ms[@style='qt-s']">
            <sch:assert test="following::ms[@style='qt-s' or @style='qt-e'][1]/@style = 'qt-e'">Milestone start missing end</sch:assert>
        </sch:rule>
        <sch:rule context="ms[@style='qt-e']">
            <sch:assert test="preceding::ms[@style='qt-s' or @style='qt-e'][1]/@style = 'qt-s'">Milestone end missing start</sch:assert>
        </sch:rule>
    </sch:pattern>
</sch:schema>
