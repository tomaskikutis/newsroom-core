import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';

import SearchBar from 'search/components/SearchBar';

class ListBar extends React.Component {
    render() {
        return (
            <section className="content-header" data-test-id={this.props.testId}>
                <nav className={classNames(
                    'content-bar navbar flex-nowrap',
                    {
                        'content-bar--side-padding': !this.props.noLeftPadding,
                        'content-bar--no-left-padding': this.props.noLeftPadding,
                    }
                )}>
                    {this.props.children}
                    {!this.props.noSearch &&
                        (<SearchBar
                            setQuery={this.props.setQuery}
                            fetchItems={() => this.props.fetch()}
                            enableQueryAction={this.props.enableQueryAction}
                        />
                        )}
                    <div className="content-bar__right">
                        {this.props.onNewItem && (
                            <button
                                data-test-id="new-item-btn"
                                className="btn btn-outline-secondary btn-responsive"
                                onClick={() => this.props.onNewItem()}
                            >
                                {this.props.buttonText}
                            </button>
                        )}
                    </div>
                </nav>
            </section>
        );
    }
}

ListBar.propTypes = {
    setQuery: PropTypes.func,
    fetch: PropTypes.func,
    buttonText: PropTypes.string.isRequired,
    onNewItem: PropTypes.func,
    children: PropTypes.node,
    noSearch: PropTypes.bool,
    noLeftPadding: PropTypes.bool,
    enableQueryAction: PropTypes.bool,
    testId: PropTypes.string,
};

ListBar.defaultProps = {enableQueryAction: true};

export default ListBar;
