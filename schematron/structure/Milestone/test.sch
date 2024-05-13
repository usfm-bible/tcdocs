<schema xmlns:sch="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt1"
    xmlns:sqf="http://www.schematron-quickfix.com/validator/process"
    xmlns="http://purl.oclc.org/dsdl/schematron">
    <ns uri="http://exslt.org/regular-expressions" prefix="re"/>
    <ns uri="http://tcdocs.bible/re" prefix="py"/>
    <pattern>
        <rule context="ms[@style='qt-s']">
            <let name="nextQt" value="following::ms[@style='qt-s' or @style='qt-e'][1]" />
            <assert test="not(following::ms[re:test(@style, 'qt[1-5]-s')])">qt-s should not be mixed with numbered qt styles</assert>
            <assert test="$nextQt/@style = 'qt-e'">Milestone start missing end</assert>
            <assert test="(./@sid = $nextQt/@eid) or (not(./@sid) and not($nextQt/@eid))">sid of start (<value-of select="./@sid" />) must match eid of end (<value-of select="$nextQt/@eid" />)</assert>
        </rule>
        <rule context="ms[@style='qt-e']">
            <let name="prevQt" value="preceding::ms[@style='qt-s' or @style='qt-e'][1]" />
            <assert test="$prevQt/@style = 'qt-s'">Milestone end missing start</assert>
            <assert test="(./@eid = $prevQt/@sid) or (not(./@eid) and not($prevQt/@sid))">sid of start must match eid of end</assert>
        </rule>
    </pattern>
    <pattern>
        <rule context="ms[re:test(@style, 'qt[1-5]\-s')]">
            <let name="nextQt" value="following::ms[re:test(@style, 'qt[1-5]\-[se]')][1]" />
            <let name="thisLevel" value="number(substring(@style, 2, 1))" />
            <let name="nextLevel" value="number(substring($nextQt/@style, 2, 1))" />
            <let name="change" value="$nextLevel - $thisLevel" />
            <assert test="($change > -2) and ($change &lt; 2)">Levels should only change by 1</assert>
            <assert test="not(following::ms[@style = 'qt-s'])">numbered qt styles should not be mixed with qt styles</assert>
            <assert test="$nextQt/@style = 'qt-e'">Milestone start missing end</assert>
            <assert test="(./@sid = $nextQt/@eid) or (not(./@sid) and not($nextQt/@eid))">sid of start (<value-of select="./@sid" />) must match eid of end (<value-of select="$nextQt/@eid" />)</assert>
        </rule>
        <rule context="ms[@style='qt-e']">
            <let name="prevQt" value="preceding::ms[@style='qt-s' or @style='qt-e'][1]" />
            <assert test="$prevQt/@style = 'qt-s'">Milestone end missing start</assert>
            <assert test="(./@eid = $prevQt/@sid) or (not(./@eid) and not($prevQt/@sid))">sid of start must match eid of end</assert>
        </rule>
    </pattern>
</schema>
