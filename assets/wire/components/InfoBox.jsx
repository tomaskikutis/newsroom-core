import React from 'react';
import PropTypes from 'prop-types';
import {bem} from 'ui/utils';
import { gettext } from 'utils';
import InfoBoxContent from './InfoBoxContent';

export default function InfoBox(props) {
    const className = bem('info-box', null, {
        'top': props.top,
    });

    return (
        <div className={className} id={props.id || null}>
            {props.label && (
                <span className="info-box__label">{gettext('{{name}}', {name: props.label})}</span>
            )}
            {React.Children.map(props.children, (element, key) => <InfoBoxContent key={key} element={element} />)}
        </div>
    );
}

InfoBox.propTypes = {
    id: PropTypes.string,
    label: PropTypes.string,
    children: PropTypes.node,
    top: PropTypes.bool,
};
