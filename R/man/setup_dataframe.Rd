% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/prophet.R
\name{setup_dataframe}
\alias{setup_dataframe}
\title{Prepare dataframe for fitting or predicting.}
\usage{
setup_dataframe(m, df, initialize_scales = FALSE)
}
\arguments{
\item{m}{Prophet object.}

\item{df}{Data frame with columns ds, y, and cap if logistic growth.}

\item{initialize_scales}{Boolean set scaling factors in m from df.}
}
\value{
list with items 'df' and 'm'.
}
\description{
Adds a time index and scales y.
}

